from django.shortcuts import render

# Create your views here.
import numpy as np
import matplotlib.pyplot as plt
from plottings import PNGValuePlot
from django.shortcuts import render
import matplotlib
matplotlib.use("Agg")

class SimplePlotToValue(PNGValuePlot):
    def plotter_function(self, data, **options):
        np.random.seed(2)
        fig, ax = plt.subplots()
        ax.plot(np.random.rand(20), '-o', ms=20, lw=2, alpha=0.7,
                mfc='orange')
        ax.grid()
        return figure


def plot(request, **kwargs):
    return render(request, "plot.html", {"plot": SimplePlotToValue()})
