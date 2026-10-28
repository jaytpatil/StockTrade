from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
import models
import schemas
import auth
from utils.stock_data import get_real_time_price

router = APIRouter()

@router.post("/buy")
def buy_stock(
    order: schemas.TradeOrder, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    symbol = order.symbol.upper().strip()
    shares = float(order.shares)

    if shares <= 0:
        raise HTTPException(status_code=400, detail="Number of shares must be greater than zero.")

    price_data = get_real_time_price(symbol)
    if price_data.get("status") != "success" or not price_data.get("current_price"):
        raise HTTPException(status_code=400, detail=f"Could not retrieve live price for {symbol}.")

    current_price = float(price_data["current_price"])
    total_cost = round(shares * current_price, 2)

    if current_user.virtual_balance < total_cost:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient virtual funds. Cost: ${total_cost:,.2f}, Available: ${current_user.virtual_balance:,.2f}"
        )

    # Deduct balance
    current_user.virtual_balance = round(current_user.virtual_balance - total_cost, 2)

    # Update or create portfolio position
    position = db.query(models.PortfolioItem).filter(
        models.PortfolioItem.user_id == current_user.id,
        models.PortfolioItem.symbol == symbol
    ).first()

    if position:
        new_total_shares = position.shares + shares
        total_invested = (position.shares * position.average_buy_price) + total_cost
        position.average_buy_price = round(total_invested / new_total_shares, 2)
        position.shares = round(new_total_shares, 4)
    else:
        position = models.PortfolioItem(
            user_id=current_user.id,
            symbol=symbol,
            company_name=f"{symbol} Corp",
            shares=round(shares, 4),
            average_buy_price=round(current_price, 2)
        )
        db.add(position)

    # Record Transaction
    txn = models.Transaction(
        user_id=current_user.id,
        symbol=symbol,
        transaction_type="BUY",
        shares=round(shares, 4),
        price_per_share=round(current_price, 2),
        total_amount=total_cost,
        timestamp=datetime.utcnow()
    )
    db.add(txn)

    db.commit()
    db.refresh(current_user)
    db.refresh(position)

    return {
        "status": "success",
        "message": f"Successfully purchased {shares} shares of {symbol} at ${current_price:.2f}",
        "symbol": symbol,
        "shares": position.shares,
        "average_buy_price": position.average_buy_price,
        "virtual_balance": current_user.virtual_balance
    }

@router.post("/sell")
def sell_stock(
    order: schemas.TradeOrder, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    symbol = order.symbol.upper().strip()
    shares = float(order.shares)

    if shares <= 0:
        raise HTTPException(status_code=400, detail="Number of shares must be greater than zero.")

    position = db.query(models.PortfolioItem).filter(
        models.PortfolioItem.user_id == current_user.id,
        models.PortfolioItem.symbol == symbol
    ).first()

    if not position or position.shares < shares:
        owned = position.shares if position else 0
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient shares to sell. You currently own {owned} shares of {symbol}."
        )

    price_data = get_real_time_price(symbol)
    if price_data.get("status") != "success" or not price_data.get("current_price"):
        raise HTTPException(status_code=400, detail=f"Could not retrieve live market price for {symbol}.")

    current_price = float(price_data["current_price"])
    total_proceeds = round(shares * current_price, 2)

    # Credit proceeds to user balance
    current_user.virtual_balance = round(current_user.virtual_balance + total_proceeds, 2)

    # Deduct position shares
    position.shares = round(position.shares - shares, 4)
    remaining_shares = position.shares
    if position.shares <= 0.0001:
        db.delete(position)
        remaining_shares = 0.0

    # Record Transaction
    txn = models.Transaction(
        user_id=current_user.id,
        symbol=symbol,
        transaction_type="SELL",
        shares=round(shares, 4),
        price_per_share=round(current_price, 2),
        total_amount=total_proceeds,
        timestamp=datetime.utcnow()
    )
    db.add(txn)

    db.commit()
    db.refresh(current_user)

    return {
        "status": "success",
        "message": f"Successfully sold {shares} shares of {symbol} at ${current_price:.2f}",
        "symbol": symbol,
        "remaining_shares": remaining_shares,
        "virtual_balance": current_user.virtual_balance
    }

@router.post("/deposit")
def deposit_virtual_currency(
    req: schemas.DepositRequest, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    amount = float(req.amount)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Deposit amount must be greater than zero.")

    current_user.virtual_balance = round(current_user.virtual_balance + amount, 2)

    txn = models.Transaction(
        user_id=current_user.id,
        symbol="CASH",
        transaction_type="DEPOSIT",
        shares=0.0,
        price_per_share=0.0,
        total_amount=round(amount, 2),
        timestamp=datetime.utcnow()
    )
    db.add(txn)
    db.commit()
    db.refresh(current_user)

    return {
        "status": "success",
        "message": f"Successfully added ${amount:,.2f} virtual funds to your balance.",
        "virtual_balance": current_user.virtual_balance
    }

@router.get("/portfolio")
def get_user_portfolio(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    positions = db.query(models.PortfolioItem).filter(
        models.PortfolioItem.user_id == current_user.id
    ).all()

    portfolio_items = []
    total_portfolio_value = 0.0

    for pos in positions:
        rt_price = pos.average_buy_price
        try:
            price_res = get_real_time_price(pos.symbol)
            if price_res.get("status") == "success" and price_res.get("current_price"):
                rt_price = float(price_res["current_price"])
        except Exception:
            rt_price = pos.average_buy_price

        current_val = round(pos.shares * rt_price, 2)
        invested_val = round(pos.shares * pos.average_buy_price, 2)
        pnl = round(current_val - invested_val, 2)
        pnl_pct = round((pnl / invested_val) * 100, 2) if invested_val > 0 else 0.0
        total_portfolio_value += current_val

        portfolio_items.append({
            "id": pos.id,
            "symbol": pos.symbol,
            "company_name": pos.company_name or pos.symbol,
            "shares": pos.shares,
            "average_buy_price": pos.average_buy_price,
            "current_price": rt_price,
            "current_value": current_val,
            "invested_value": invested_val,
            "profit_loss": pnl,
            "profit_loss_pct": pnl_pct
        })

    txns = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    ).order_by(models.Transaction.timestamp.desc()).limit(20).all()

    formatted_txns = [{
        "id": t.id,
        "symbol": t.symbol,
        "type": t.transaction_type,
        "shares": t.shares,
        "price_per_share": t.price_per_share,
        "total_amount": t.total_amount,
        "timestamp": t.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    } for t in txns]

    cash_balance = round(current_user.virtual_balance, 2)
    net_worth = round(cash_balance + total_portfolio_value, 2)

    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name or "Trader",
            "is_guest": getattr(current_user, "is_guest", False),
            "virtual_balance": cash_balance
        },
        "cash_balance": cash_balance,
        "portfolio_value": round(total_portfolio_value, 2),
        "net_worth": net_worth,
        "positions": portfolio_items,
        "transactions": formatted_txns
    }
