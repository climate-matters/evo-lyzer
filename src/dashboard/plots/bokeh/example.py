"""This is an example."""
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature

from src.dashboard.plots import bh


@bh.register('/bkapp')
def bkapp(doc):
    df = sea_surface_temperature.copy()
    source = ColumnDataSource(data=df)
    plot = figure(x_axis_type='datetime', y_range=(0, 25), y_axis_label='Temperature (Celsius)',
                  title="Sea Surface Temperature at 43.18, -70.43")
    plot.line('time', 'temperature', source=source)

    def callback(attr, old, new):
        if new == 0:
            data = df
        else:
            data = df.rolling("{}D".format(new)).mean()
        source.data = ColumnDataSource.from_df(data)

    slider = Slider(start=0, end=30, value=0, step=1, title="Smoothing by N Days")
    slider.on_change('value', callback)
    doc.add_root(column(slider, plot))
    # doc.theme = Theme(filename="theme.yaml")
