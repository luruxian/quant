"""
自定义绩效分析器
"""
import backtrader as bt


class PerformanceAnalyzer(bt.Analyzer):
    """
    绩效分析器 - 计算交易统计指标
    
    输出：
    - total_trades: 总交易数
    - winning_trades: 盈利交易数
    - losing_trades: 亏损交易数
    - win_rate: 胜率
    - profit_factor: 盈亏比
    - total_pnl: 总盈亏
    - avg_win: 平均盈利
    - avg_loss: 平均亏损
    - avg_holding_days: 平均持仓天数
    """
    
    def __init__(self):
        self.win_trades = 0
        self.loss_trades = 0
        self.total_pnl = 0
        self.gross_profit = 0
        self.gross_loss = 0
        self.holding_days = []
        
    def notify_trade(self, trade):
        """当交易完成时调用"""
        if trade.isclosed:
            self.total_pnl += trade.pnl
            
            if trade.pnl > 0:
                self.win_trades += 1
                self.gross_profit += trade.pnl
            else:
                self.loss_trades += 1
                self.gross_loss += abs(trade.pnl)
            
            # 计算持仓天数
            if hasattr(trade, 'open') and hasattr(trade, 'close'):
                open_dt = trade.open.datetime
                close_dt = trade.close.datetime
                if hasattr(open_dt, 'date') and hasattr(close_dt, 'date'):
                    days = (close_dt.date() - open_dt.date()).days
                    self.holding_days.append(days)
    
    def get_analysis(self):
        """返回分析结果"""
        total_trades = self.win_trades + self.loss_trades
        win_rate = self.win_trades / total_trades if total_trades > 0 else 0
        profit_factor = self.gross_profit / self.gross_loss if self.gross_loss > 0 else float('inf')
        avg_win = self.gross_profit / self.win_trades if self.win_trades > 0 else 0
        avg_loss = self.gross_loss / self.loss_trades if self.loss_trades > 0 else 0
        avg_holding = sum(self.holding_days) / len(self.holding_days) if self.holding_days else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': self.win_trades,
            'losing_trades': self.loss_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_pnl': self.total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_holding_days': avg_holding,
        }


class DrawDownAnalyzer(bt.Analyzer):
    """
    回撤分析器 - 计算最大回撤和回撤曲线
    
    输出：
    - max_drawdown: 最大回撤 (百分比)
    - max_drawdown_money: 最大回撤金额
    - drawdown_curve: 回撤曲线数据
    """
    
    def __init__(self):
        self.max_drawdown = 0
        self.max_drawdown_money = 0
        self.drawdown_curve = []
        self.peak = 0
        
    def next(self):
        """每个 bar 调用"""
        portfolio_value = self.strategy.broker.getvalue()
        
        # 更新峰值
        if portfolio_value > self.peak:
            self.peak = portfolio_value
        
        # 计算回撤
        if self.peak > 0:
            drawdown_money = self.peak - portfolio_value
            drawdown_pct = drawdown_money / self.peak
            
            self.max_drawdown = max(self.max_drawdown, drawdown_pct)
            self.max_drawdown_money = max(self.max_drawdown_money, drawdown_money)
            
            # 记录回撤曲线
            dt = self.strategy.datas[0].datetime.date(0)
            self.drawdown_curve.append({
                'date': dt.strftime('%Y-%m-%d'),
                'drawdown': -drawdown_pct,  # 负值表示回撤
            })
    
    def get_analysis(self):
        return {
            'max_drawdown': -self.max_drawdown,  # 转为负值
            'max_drawdown_money': -self.max_drawdown_money,
            'drawdown_curve': self.drawdown_curve,
        }
