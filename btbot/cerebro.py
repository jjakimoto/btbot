import backtrader as bt


class Cerebro(bt.Cerebro):
    def plot(self, plotter=None, numfigs=1, iplot=True, start=None, end=None,
         width=16, height=9, dpi=300, tight=True, use=None, path=None,
         **kwargs):
        '''
        Plots the strategies inside cerebro

        If ``plotter`` is None a default ``Plot`` instance is created and
        ``kwargs`` are passed to it during instantiation.

        ``numfigs`` split the plot in the indicated number of charts reducing
        chart density if wished

        ``iplot``: if ``True`` and running in a ``notebook`` the charts will be
        displayed inline

        ``use``: set it to the name of the desired matplotlib backend. It will
        take precedence over ``iplot``

        ``start``: An index to the datetime line array of the strategy or a
        ``datetime.date``, ``datetime.datetime`` instance indicating the start
        of the plot

        ``end``: An index to the datetime line array of the strategy or a
        ``datetime.date``, ``datetime.datetime`` instance indicating the end
        of the plot

        ``width``: in inches of the saved figure

        ``height``: in inches of the saved figure

        ``dpi``: quality in dots per inches of the saved figure

        ``tight``: only save actual content and not the frame of the figure
        '''
        if self._exactbars > 0:
            return

        if not plotter:
            from backtrader import plot
            if self.p.oldsync:
                plotter = plot.Plot_OldSync(**kwargs)
            else:
                plotter = plot.Plot(**kwargs)

        # pfillers = {self.datas[i]: self._plotfillers[i]
        # for i, x in enumerate(self._plotfillers)}

        # pfillers2 = {self.datas[i]: self._plotfillers2[i]
        # for i, x in enumerate(self._plotfillers2)}
        import matplotlib.pyplot as plt
        figs = []
        for stratlist in self.runstrats:
            for si, strat in enumerate(stratlist):
                rfig = plotter.plot(strat, figid=si * 100,
                                numfigs=numfigs, iplot=iplot,
                                start=start, end=end, use=use)
                # pfillers=pfillers2)

                figs.append(rfig)
            fig = plt.gcf()
            plotter.show()
        fig.set_size_inches(width, height)
        if path:
            fig.savefig(path, dpi=dpi)
        return figs


def get_cerebro(startcash=10000):
    cerebro = Cerebro()
    cerebro.broker.setcash(startcash)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='sharpe',
                        timeframe=bt.analyzers.TimeFrame.Days)
    cerebro.addobserver(bt.observers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    return cerebro