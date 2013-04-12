'''
tradesignal/models.py v0.1 130110

Created on 20120907

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

from django.db import models, transaction

from utils_python.utils import div
from pricemanager.models import Stock
from metasystem.parameters.fields import _Param


class Trade(models.Model):
    '''
    This table holds signals. They are usually trades, but in certain cases may
    be positions or signals.
    '''
    system = models.ForeignKey('system.System')
    stock = models.ForeignKey(Stock)
    method = models.ForeignKey('metasystem.Method') # direction is in Method
    volume = models.PositiveIntegerField(null=True)
    rule_entry = models.CharField(max_length=10)
    price_entry = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    date_entry = models.DateField(null=True)
    rule_exit = models.CharField(max_length=10, null=True)
    price_exit = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    date_exit = models.DateField(null=True)


    def stoploss(self):
        '''
        Return a custom stop loss for open trades, if it has been defined. 
        The custom stop loss is defined as the low on <date_exit> + an increase
        based on an annual angle that is stored in <price_exit>.
        '''
        if self.rule_exit is not None:
            raise ValueError('This is a closed trade, stop loss does not exist')
        if self.price_exit is None or self.date_exit is None:
            return None # It is an open trade, but no stop loss is defined.
        latest_date = self.stock.get_latest_date()
        # only set the date_range of the stock if it is not set:
        if not self.stock.has_date_range() or (
                self.date_entry < self.stock.date_range[0]):
            self.stock.date_range = (self.date_entry, latest_date)
        n_days = self.stock.price.close.delta(self.date_exit, latest_date)
        ppa = float(self.price_exit) # percentage per year (angle)
        ppd = (1 + 0.01 * ppa) ** (1 / 252) #percentage per day
        return self.stock.price.low[self.date_exit] * ppd ** (n_days + 1)


    def gain(self):
        '''
        Return the % gain of this trade, in case it is an open trade (portfolio
        position), return the % gain between the entry and the latest price.
        '''
        if self.rule_exit is None:
            exit_price = self.stock.lastclose()
        else:
            exit_price = float(self.price_exit)
        return self.method.direction * 100 * (exit_price /
                float(self.price_entry) - 1)


    @classmethod
    def write_to_db(cls, signals, system):
        '''
        Writes <signals> to the database table where <signals> is a list of 
        subclasses of _BaseSignal (EntrySignals, (Positions) positions, 
        ExitSignals or trades).
        '''
        with transaction.commit_on_success():
            for signal in signals:
                data = signal.get_data()
                data['system'] = system
                cls.objects.create(**data)



class Trades(object):
    '''
    This class maintains the history of trades.

    The trade history is a list of trades. Each trade is an executed exit 
    signal, where each exit signal is an instance of the ExitSignal class.
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.clear()


    def clear(self):
        '''
        Clears all trades. Use this to start a new system without generating a
        new Trades instance.
        '''
        self.trades = []
        self.data = None


    def append(self, trade):
        '''
        Append <trade> to the list <self.trades>.
        '''
        self.trades.append(trade)


    def extend(self, trades):
        '''
        Extend the list <self.trades> with <trades>
        '''
        self.trades.extend(trades)


    def calc_performance(self, startdate, enddate, max_pos):
        '''
        Return a dict with standard performance parameters from [trades].

        NOTE: if the open positions in the positions need to be part of the 
        performance data, call the <Trades.extend> method with the argument
        <Positions.close> before this one.
        '''
        self.data = {'max_pos': max_pos, 'max_win': 0, 'max_loss': 0, 
                     'max_n_loss': 0, 'max_n_win': 0}
        n_win = n_loss = total_win = total_loss = total_days = 0
        consec_win = consec_loss = 0
        profits = []
        cum_gains = []
        prevgain = 1
        for trade in self.trades:
            # if trade.is_entrysignal: continue
            total_days += trade.n_days()
            gain = trade.gain() # gain is a fraction: 1.0 means 0 profit
            new_gain = prevgain * gain
            cum_gains.append(new_gain)
            prevgain = new_gain
            profit = 100 * (gain - 1.)
            profits.append(profit)
            if profit > 0:
                n_win += 1
                total_win += profit
                self.data['max_win'] = max(self.data['max_win'], profit)
                consec_loss = 0
                consec_win += 1
            else:
                n_loss += 1
                total_loss -= profit
                self.data['max_loss'] = max(self.data['max_loss'], -profit)
                consec_loss += 1
                consec_win = 0
            self.data['max_n_loss'] = max(consec_loss, self.data['max_n_loss'])
            self.data['max_n_win'] = max(consec_win, self.data['max_n_win'])
        self.data['avg_win'] = div(total_win, n_win)
        self.data['avg_loss'] = div(total_loss, n_loss)
        n_total = n_win + n_loss
        self.data['reliability'] = 100. * div(n_win, n_total)
        self.data['profit_factor'] = div(total_win, total_loss)
        total_profit = total_win - total_loss
        self.data['expectancy'] = div(total_profit, n_total)
        variance = ((x - self.data['expectancy'])**2 for x in profits)
        self.data['std_dev'] = div(sum(variance), n_total) ** 0.5
        self.data['sqn'] = div(self.data['expectancy'], self.data['std_dev'])
        if self.data['sqn'] is not None: 
            self.data['sqn'] *= (n_total ** 0.5 if n_total < 100 else 10.)
        self.data['days_p_trade'] = div(total_days, n_total)
        self.data['exp_p_day'] = div(self.data['expectancy'], 
                                                    self.data['days_p_trade'])
        n_years = (enddate - startdate).days / 365.
        self.data['profit_pa'] = div(total_profit, n_years * max_pos)
        self.data['true_avg_loss'] = div(total_loss, n_total)
        self.data['trades_pa'] = int(n_total / n_years + 0.499999)
        self.data['profit_ratio'] = div(self.data['profit_pa'], 
                        self.data['true_avg_loss'] * self.data['trades_pa'])

        for key in self.data:
            if isinstance(self.data[key], float): 
                self.data[key] = min (self.data[key], 999.99)
                self.data[key] = max (self.data[key], -999.99)


    def show(self):
        print 'Ntrades = ', len(self.trades)
        for trade in self.trades:
            print trade.show()


    def write_to_db(self, system):
        '''
        Writes <self.trades> to the <Trade> database table
        '''
        Trade.write_to_db(self.trades, system)



class Positions(object):
    '''
    This class maintains the positions of positions.

    The positions is a list of positions. Each position is an executed entry
    signal, where the entry signal is an instance of the EntrySignal class.
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.clear()


    def clear(self):
        '''
        Clears the positions. Use this to start a new system without generating
        a new Positions instance.
        '''
        self.positions = []
        self.max_positions = 0


    def size(self, method=None):
        '''
        Returns the number of positions in the positions. If <method> is
        specified, only the positions for that <method> are counted.
        '''
        if method:
            return sum(p.method == method for p in self.positions)
        else:
            return len(self.positions)


    def has(self, stock, method=None):
        '''
        Returns True if <stock> is in the positions, False otherwise.
        If <method> is specified, only positions for that method are 
        considered.
        '''
        if method:
            return stock in (p.stock for p in self.positions if 
                                                            p.method == method)
        else:
            return stock in (p.stock for p in self.positions)


    def get(self):
        '''
        Returns the positions as a list of positions.
        '''
        return self.positions


    def get_position(self, stock):
        '''
        Returns the position (signal) of <stock>
FIXME: AAD: what if multiple??
        '''
        pos_list = [p for p in self.positions if p.stock == stock]
        if len(pos_list) == 1:
            return pos_list[0]
        else:
            raise ValueError('position for {} not found', stock.name)


    def open_position(self, position):
        '''
        Opens a new position in the positions and returns the required cash.
        '''
        self.positions.append(position)
        return position.cashflow()


    def _index(self, stock, method=None):
        '''
        Returns the index of <stock> in <self.positions>. If <method> is 
        specified, this must also be the method .
        If <stock> is not found, None is returned
        WARNING: the return value may be 0, so DO NOT USE this method to test
        if <stock> is in the positions, use <positions.has()> for that.
        '''
        for i, position in enumerate(self.positions):
            if position.is_for(stock, method):
                return i


    def close_position(self, position):
        '''
        Closes a position in the positions and returns the cash result.
        '''
        index = self._index(position.stock, position.method)
        if index is None:
            raise AttributeError, 'Attempt to exit position that is not in the'\
                    ' positions'
        del self.positions[index]
        return position.cashflow()


    def close_all(self, date):
        '''
        Close all open positions (usually at the end of the backtest), so that 
        they are included in the performance calculation.
        Note equity (and results calculations) automatically include open 
        positions.
        '''
        trades = []
        for position in self.get():
            signal = ExitSignal(position, 'open', _Param.CLOSE)
            enddate = position.stock.price.close.latest_date_before(date)
            signal.execute(enddate)
            self.close_position(signal)
            trades.append(signal)
        return trades


    def value(self, date):
        '''
        Returns the value of the positions on <date>.
        '''
        self.max_positions = max(self.max_positions, self.size())
        value = 0
        for position in self.positions:
            if position.method.direction == position.method.LONG:
                value += position.volume * position.stock.price.close[date]
            else: #so it is short
                value += position.volume * (2 * position.price_entry -
                        position.stock.price.close[date])
        return value


    def stop_loss_risk(self, date):
        '''
        Return the sum of the Stop Loss Risk (SLR) of all positions.
        See <EntrySignal.stop_loss_risk> for definitions.
        '''
        return sum(p.stop_loss_risk(date) for p in self.positions)


    def equity_risk(self, date):
        '''
        Return the sum of the Equity Risk (ER) of all positions.
        See <EntrySignal.equity_risk> for definitions.
        '''
        return sum(p.equity_risk(date) for p in self.positions)


    def show(self):
        print 'N=', len(self.positions)
        for trade in self.positions:
            print trade.show()


    def write_to_db(self, system):
        '''
        Writes <self.positions> to the <Trade> database table
        '''
        Trade.write_to_db(self.positions, system)


'''
The following table shows which properties of each of the Signal classes are
(must be) available in each of the 4 signal 'modes'. Note that a positions
position is an EntrySignal with some extra properties and a Trade is an 
ExitSignal with some extra properties.
<at> and <price> *only* exist for true signals.

                Entry   Positions  Exit    Trade
                Signal  position   Signal
_BaseSignal
    stock          x        x        x        x
    method         x        x        x        x
    price          x        -        x        -
    (_)at          x        -        x        -
    rule_entry     x        x        x        x
EntrySignal
    price_entry             x        x        x
    date_entry              x        x        x
    volume                  x        x        x
ExitSignal
    rule_exit                        x        x
    price_exit                                x
    date_exit                                 x
'''


class _BaseSignal(object):
    '''
    Class with common methods and properties for the EntrySignal and ExitSignal
    classes.
    '''

    def __init__(self, stock, method, rule, at, price=None):
        '''
        Create a signal.
        '''
        if price is None and (at == _Param.LIMIT or at == _Param.STOP):
            raise ValueError('Price is not specified for a conditional entry.')
        if price and  (at == _Param.OPEN or at == _Param.CLOSE):
            raise ValueError('A price is specified for an unconditional entry')
        self.stock = stock
        self.method = method
        self.rule_entry = rule
        self.price = price
        self.at = at


    @property
    def at(self):
        '''
        Specify when this signal is to be executed: at the open, close, limit
        or stop. 
        '''
        return self._at

    @at.setter
    def at(self, value):
        if value not in {_Param.OPEN, _Param.CLOSE, _Param.LIMIT, _Param.STOP}:
            raise ValueError('{} is an illegal value for at.'.format(value))
        self._at = value

    @at.deleter
    def at(self):
        del self._at


    def is_unconditional(self):
        '''
        Returns true if the signal is unconditional.
        Convenience method.
        '''
        return self.price is None

    def is_conditional(self):
        '''
        Returns true if the signal is not unconditional.
        Convenience method.
        '''
        return self.price is not None


    def is_entry_signal(self):
        '''
        Returns true if the signal is an entry signal.
        '''
        return not hasattr(self, 'date_entry')


    def is_exit_signal(self):
        '''
        Returns true if the signal is an exit signal.
        '''
        return hasattr(self, 'rule_exit') and not hasattr(self, 'date_exit')


    def is_position(self):
        '''
        Returns true if the signal is a Positions position.
        '''
        return hasattr(self, 'date_entry') and not hasattr(self, 'rule_exit')


    def is_trade(self):
        '''
        Returns true if the signal is a trade.
        '''
        return hasattr(self, 'date_exit')


    def is_for(self, stock, method=None):
        '''
        Returns true if the current signal is for <stock> and <method>.
        '''
        return self.stock == stock and (method is None or self.method == method)


    def get_data(self):
        '''
        Returns a dict with key:value pairs for all properties that need to be
        stored in the database.
        '''
        data_dict = {}
        for key in ('stock', 'method', 'volume', 'rule_entry', 'price_entry',
                    'date_entry', 'rule_exit', 'price_exit', 'date_exit'):
            data_dict[key] = getattr(self, key, None)
        price = getattr(self, 'price', None)
        if price:
            if not data_dict['price_entry']:
                data_dict['price_entry'] = price
            elif not data_dict['price_exit']:
                data_dict['price_exit'] = price
            else:
                raise ValueError('price was set and p_N and p_X were set')
        return data_dict


    def _execute(self, date, entry=False):
        '''
        Returns the price if this signal was executed on <date>. Returns None
        if the signal was not executed or it was not a trading day.

        long  entry stop  : >= price (buy breakout up)
        long  entry limit : <= price (buy up to)
        short entry stop  : <= price (sell breakout down)
        short entry limit : >= price (sell down to)
        long  exit  stop  : <= price (sell stop loss)
        long  exit  limit : >= price (sell take profit)
        short exit  stop  : >= price (buy stop loss)
        short exit  limit : <= price (buy take profit)
        '''
        if self.at == _Param.OPEN:
            return self.stock.price.open.on(date)
        elif self.at == _Param.CLOSE:
            return self.stock.price.close.on(date)
        elif (self.method.direction == self.method.LONG) == (entry == (
                self.at == _Param.LIMIT)):
            # LONG  entry: buy  <= limit price (buy up to)
            # LONG  exit:  sell <= stop price  (stop loss)
            # SHORT entry: sell <= stop price  (breakout)
            # SHORT exit:  buy  <= limit price (take profit)
            low = self.stock.price.low.on(date)
            open_ = self.stock.price.open.on(date)
            return min(open_, self.price) if (low and open_ and 
                    low < self.price) else None
        else:
            # LONG  exit:  sell >= limit price (take profit)
            # LONG  entry: buy  >= stop price  (breakout)
            # SHORT exit:  buy  >= stop price  (stop loss)
            # SHORT entry: sell >= limit price (buy up to)
            high = self.stock.price.high.on(date)
            open_ = self.stock.price.open.on(date)
            return max(open_, self.price) if (high and open_ and 
                    high > self.price) else None


    def show(self):
        '''
        Returns a string that contains the parameters of this signal.
        '''
        text = ''
        for key in self.KEYLIST:
            text += '-{}-\t'.format(getattr(self, key, ''))
        return text


class EntrySignal(_BaseSignal):
    '''
    Entry signal that may or may not be executed, depending on whether it is
    conditional or unconditional.
    If it is executed it becomes a positions position.
    '''

    KEYLIST = ('stock', 'method', 'volume', 'rule_entry', 'price_entry', 
            'date_entry', '_at', 'price')

    _stoploss = {} # cached value for get_stop

    def get_price(self, date):
        '''
        Returns the price of the entry signal (before execution). If no price is
        set, the close price on <date> is used as an estimate of the entry 
        price.
        '''
        if not self.is_entry_signal():
            raise AttributeError('get_price must only be used on EntrySignals')
        if self.price:
            return self.price
        else:
            return self.stock.price.close[date]


    def execute(self, date):
        '''
        Try to execute this signal on <date>
        The signal is only executed if it is a trading day

        If the entry signal is executed, the signal becomes a position.
        '''
        price = self._execute(date, entry=True)
        if price:
            self.price_entry = price
            self.date_entry = date
            del self.at
            del self.price
            return True # entrysignal has now 'become' a position (so a 
                        #    position is an instance of an entrysignal
        return False


    def cashflow(self):
        '''
        Return the cashflow of the entry. Note that regardless of whether a 
        trade is long or short, the entry will always result in negative 
        cashflow.
        '''
        return - self.volume * self.price_entry


    def get_stop(self, date):
        '''
        Return the stop(loss) value (price) for the trading day after <date>.
        The value is cached to prevent multiple identical calculations.
        '''
        if date not in self._stoploss:
            stop_loss = 0
            dummy = DummyPosition(self.stock, self.method, date)
            for exit_ in self.method.exits:
                exit_signal = exit_.params.signal(date=date, position=dummy)
                if exit_signal.at == _Param.STOP:
                    stop_loss = max(stop_loss, exit_signal.price)
            if not stop_loss:
                raise ValueError('No stop loss is defined for this entry')
            self._stoploss = {date: stop_loss}
        return self._stoploss[date]


    def stop_loss_risk(self, date, volume=None):
        '''
        Return the Stop Loss Risk (SLR) of this entry signal or position. SLR is
        the loss that would be made on a trade if the stock would sell on the
        next day for its stop loss price. If the stop loss is above the entry
        price, SLR = 0.
        If it is an entry signal (no position), SLR is estimated, instead of
        using <self.price_entry> (which is not known yet).
        Note that SLR is a positive number.
        '''
        if not volume and self.volume:
            volume = self.volume
        else:
            raise ValueError('volume not set for this signal/position')
        stop_loss = self.get_stop(date)
        price = self.price_entry if self.is_position() else self.get_price(date)
        slr = volume * (price - stop_loss) if stop_loss < price else 0
        return slr


    def equity_risk(self, date, volume=None):
        '''
        Return the Equity Risk (ER) of this entry signal or position. ER is
        the loss that would be made, relative to todays close, on a trade if the
        stock would sell on the next day for its stop (loss) price.
        Note that ER is a positive number.
        '''
        if not volume and self.volume:
            volume = self.volume
        else:
            raise ValueError('volume not set for this signal/position')
        return volume * (self.stock.price.close[date] - self.get_stop(date))


class DummyPosition(EntrySignal):

    def __init__(self, stock, method, date):
        super(DummyPosition, self).__init__(stock, method, 'dummy', _Param.OPEN)
        self.price_entry = 0
        self.date_entry = date
        self.volume = 1
        del self.at
        del self.price


class ExitSignal(_BaseSignal):
    '''
    Exit signal that may or may not be executed, depending on whether it is
    conditional or unconditional.
    If it is executed it becomes a trade.
    An exit signal is instantiated from a positions position.
    '''

    KEYLIST = ('stock', 'method', 'volume', 'rule_entry', 
            'price_entry', 'date_entry', 'rule_exit', 'price_exit',
            'date_exit', '_at', 'price')


    def __init__(self, position, rule, at, price=None):
        '''
        Create the exit signal.
        '''
        if not hasattr(position, 'volume'):
            # If volume does not exist, <position> is an entry signal, so an
            #  empty instance of ExitSignal is created to indicate that an exit
            #  signal exists for this entry signal.
            return
        super(ExitSignal, self).__init__(position.stock, position.method,
                position.rule_entry, at, price)
        self.price_entry = position.price_entry
        self.date_entry = position.date_entry
        self.rule_exit = rule
        # copy additional position properties:
        self.volume = position.volume


    def n_days(self):
        '''
        Returns the number of days this trade was on the market.
        '''
        if self.is_trade():
            return self.stock.price.close.delta(
                    self.date_entry, self.date_exit)
        else:
            raise TypeError('get_n_days only works on trades')


    def gain(self):
        '''
        Returns the number of days this trade was on the market.
        '''
        if self.is_trade():
            return 1 +  self.method.direction * (
                    self.price_exit / self.price_entry - 1)
        else:
            raise TypeError('get_profit only works on trades')


    def get_price(self, date):
        '''
        Returns the price of the exit signal (before execution). If no price is
        set, the close price on <date> is used as an estimate of the entry 
        price.
        '''
        if not self.is_exit_signal():
            raise AttributeError('get_price must only be used on ExitSignals')
        if self.price:
            return self.price
        else:
            return self.stock.price.close[date]


    def execute(self, date):
        '''
        Try to execute this signal on <date>
        The signal is only executed if it is a trading day

        If the exit signal is executed, the signal becomes a trade.
        '''
        price = self._execute(date)
        if price:
            self.price_exit = price
            self.date_exit = date
            del self.at
            del self.price
            return True # exitsignal has now 'become' a trade, so a trade is
                        #    an instance of ExitSignal
        return False


    def is_for(self, stock, method=None):
        '''
        Returns true if the current exit signal is for the same stock and 
        method as <position>.
        '''
        return super(ExitSignal, self).is_for(stock, method)


    def cashflow(self):
        '''
        Returns the cashflow of the exit. Note that regardless of whether a 
        trade is long or short, the exit will always result in positive 
        cashflow.
        '''
        if self.method.direction == self.method.LONG:
            return self.volume * self.price_exit
        else: # so it is short
            return self.volume * (2 * self.price_entry - self.price_exit)



class Signals(object):
    '''
    This class manages the list of entry and exit signals.
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.clear()


    def clear(self):
        '''
        Clears the positions. Use this to start a new system without generating
        a new Positions instance.
        '''
        self.signals = []


    @property
    def exits(self):
        '''
        Return the list of exit signals
        '''
        return [s for s in self.signals if s.is_exit_signal()]


    @property
    def entries(self):
        '''
        Return a list with all entry signals
        '''
        return [s for s in self.signals if s.is_entry_signal()]


    def set_entries(self, date, method, pool, positions):
        '''
        Generate entry signals on <date> for the day after <date>
        If an unconditional entry signal is generated, all conditional entries
        for the same stock are removed.
        '''
        for (stock, unused, valid) in method.get_ranked_stocklist(date, pool):
            if positions.has(stock, method) or not valid:
                continue
            for entry in method.entries:
                signal = entry.params.signal(date=date, stock=stock, 
                        method=method)
                if not signal:
                    continue
                # Discard the entry signal if there would be an exit signal on
                #  the same day for the same stock and method:
                for exit_ in method.exits:
                    if exit_.params.can_prevent_entry and \
                            exit_.params.signal(date=date, position=signal):
                        signal = None
                        break   # one exit signal suffices to discard the entry
                if not signal:
                    continue
                self.signals.append(signal)
                if signal.is_unconditional():
                    self._remove_conditional_signals(self.entries, stock, method)
                    break # prevent multiple entries with the same method


    def set_exits(self, date, positions, pool, method_list):
        '''
        Generate exit signals on <date>.
        Generating exit signals is always the first step, so the list is cleared
        first.
        If an unconditional exit signal is generated, all conditional signals
        for the same stock are removed.
        '''
        self.clear()
        for position in positions.get():
            method = position.method
            for exit_ in method.exits:
                signal = exit_.params.signal(date=date, position=position, 
                        ranked_stock_list=method.get_ranked_stocklist(date, 
                        pool), method_list=method_list)
                if signal:
                    self.signals.append(signal)
                    if signal.is_unconditional():
                        self._remove_conditional_signals(self.exits, 
                                position.stock, method)
                        break # no need for other exits for this stock


    def set_volume(self, date, allocation, equity, equitymodel, positions):
        '''
        calculate the volume for every entry signal in <self.signals> until the 
        equity model does not allow further entries.
        '''
        for entry_signal in self.entries:
            # calculated the allocated for this entry signal
            volume = allocation.size(date=date, entry_signal=entry_signal, 
                    total_equity=equity.total[date])
            # check if the equity model allows the calculated allocation
            volume = equitymodel.adjust_volume(date=date, signals=self, 
                    volume=volume, cash=equity.cash[date], positions=positions,
                    entrysignal=entry_signal, total_equity=equity.total[date])
            if volume <= 0:
                volume = 0
                break # for all remaining entry signals volume = 0 so they
                    # will be ignored
            entry_signal.volume = volume
        self._remove_empty_entries()


    def entries_cash(self, date):
        '''
        Returns the (estimated) required cash to enter all entry signals that 
        have their volume set. These may be conditional or unconditional.
        '''
        return sum((n.volume * n.get_price(date) for n in self.entries if 
                hasattr(n, 'volume')))


    def exits_cash(self, date):
        '''
        Returns an estimate of cash that would be freed up by all unconditional
        exit signals.
        '''
        return sum((x.volume * x.get_price(date) for x in self.exits if 
                x.is_unconditional()))


    def stop_loss_risk(self, date):
        '''
        Return the sum of the Stop Loss Risk (SLR) of all entry signals that
        have their volume set.
        See <EntrySignal.stop_loss_risk> for definitions.
        '''
        slr = 0
        for entry_signal in self.entries:
            if entry_signal.volume:
                slr += entry_signal.stop_loss_risk(date)
        return slr


    def equity_risk(self, date):
        '''
        Return the sum of the Equity Risk (ER) of all entry signals that have
        their volume set.
        See <EntrySignal.equity_risk> for definitions.
        '''
        er = 0
        for entry_signal in self.entries:
            if entry_signal.volume:
                er += entry_signal.equity_risk(date)
        return er


    def _remove_empty_entries(self):
        '''
        Remove all entry signals from the list that have no volume.
        '''
        for entry_signal in reversed(self.entries):
            if not hasattr(entry_signal, 'volume'):
                self.signals.remove(entry_signal)


    def trade(self, date, positions, equity):
        '''
        Execute all entry and exit signals in <self> using <date>'s prices.
        Any resulting trades may lead to updates of <positions>, <trades> and
        <equity>.
        '''
        trades = []
        cashflow = 0
        for signal in self.exits:
            if not positions.has(signal.stock, signal.method):
                continue # prevent exiting the same position twice
            if signal.execute(date):
                cashflow += positions.close_position(signal)
                trades.append(signal)
        for signal in self.entries:
            if signal.execute(date):
                cashflow += positions.open_position(signal)
        equity.update(date, cashflow, positions.value(date))
        return trades


    def _remove_conditional_signals(self, signals, stock, method):
        '''
        Remove existing conditional <signals> (entries or exits) for <position>
        '''
        for signal in reversed(signals):
            if signal.is_conditional() and signal.is_for(stock, method):
                self.signals.remove(signal)


    def count_executable_entries(self):
        '''
        Return the number of entries that have their volume set.
        '''
        return len([n for n in self.entries if hasattr(n, 'volume')])


    def count_unconditional_exits(self, method=None):
        '''
        Return the number of unconditional exit signals.
        '''
        if method:
            return sum(1 for s in self.exits if s.is_unconditional() and 
                    s.method == method)
        else:
            return sum(1 for s in self.exits if s.is_unconditional())
