import matplotlib.pyplot as plt
import matplotlib.markers as markers
import warnings
import json
import pandas as pd

def plot_isotherm(isotherm_json,suptitle=None,figsize=(10,6)):
    '''
    Plot all isotherms with a default settings for legend, colors and markers.

    Args:
        isotherm_json (str): Path to the file with isotherm post-processed data in JSON format.
    '''
    warnings.filterwarnings("ignore") 
    with open(isotherm_json,"r") as f:
        file_contents = f.read()
    parsed_json = json.loads(file_contents)

    df_json = pd.DataFrame(parsed_json["isotherms"])
    n_isotherms = df_json.shape[0]
    legends = []
    cmap = plt.colormaps['tab20']
    colors  = [cmap(i) for i in range(n_isotherms)]
    ms = list(markers.MarkerStyle.markers)[:n_isotherms]
    fig,ax = plt.subplots(figsize=figsize)
    x = "Pressure(Pa)"
    y = "uptake(cm^3 (STP)/cm^3 framework)"
    for i,row in df_json.iterrows():
        isotherm = pd.DataFrame({x:row[x],y:row[y]})
        isotherm.plot(x=x,y=y,kind='line',ax= ax,color=colors[i],legend=False)
        isotherm.plot(x=x,y=y,kind='scatter',ax= ax,color=colors[i],marker=ms[i])
        legends.append(','.join(map(str,row[['structure','molecule_name','temperature']].values)))

    # Creating legend handles with both marker symbol and label and display it
    handles = []
    for i in range(n_isotherms):
        handle = plt.Line2D([], [], color=colors[i], marker=ms[i], markersize=6, label=legends[i])
        handles.append(handle)
    _ = ax.legend(handles=handles, bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.suptitle(suptitle,y=0.95)
    fig.tight_layout()
    plt.show(block=False)
