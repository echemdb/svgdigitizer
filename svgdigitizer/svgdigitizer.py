from svg.path import parse_path
from xml.dom import minidom
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

class SvgData:
    def __init__(self, filename, xlabel=None, ylabel=None):
        '''filename: should be a valid svg file created according to the documentation'''
        self.filename = filename
        
        self.xlabel = xlabel or 'x'
        self.ylabel = ylabel or 'y'
        
        self.doc = minidom.parse(self.filename)

        self.figpaths = self.get_paths()
        
        self.ref_points, self.real_points = self.get_points()
        
        self.xtrafo = self.get_trafo([self.ref_points['x1'][0], self.ref_points['x2'][0]], [self.real_points['x1'], self.real_points['x2']])
        self.ytrafo = self.get_trafo([self.ref_points['y1'][1], self.ref_points['y2'][1]], [self.real_points['y1'], self.real_points['y2']])
        
        self.doc.unlink()
        self.get_parsed()
        self.create_df()
        
    
    def get_points(self):
        '''Creates:
        ref_points: relative values of the spheres/eclipses in the svg file.
        real_points: real values of the points given in the title text of the svg file.'''
        ref_points = {}
        real_points = {}
        
        for shape in ['circle', 'ellipse']:
            for path in self.doc.getElementsByTagName(shape):
                title = path.getElementsByTagName("title")
                titletext = title[0].firstChild.data
                position, value = titletext[:2], float(titletext[3:])
                
                ref_points[position] = [float(path.getAttribute('cx')), float(path.getAttribute('cy'))] 
                real_points[position] = value
        
        print('Ref points: ', ref_points)
        print('point values: ',real_points)
        return ref_points, real_points
        
    def get_parsed(self):
        '''cuve function'''
        self.allresults = {}
        for pathid, pvals in self.figpaths.items():
            self.allresults[pathid] = self.get_real_values(pvals)
    

    def get_trafo(self, xrefpath, xrefvalues):
        # we assume a rectangular plot
        # xvalue = mrefx * (xpath -xrefpath0 ) + xrefvalue0
        print('xrefpath ', xrefpath, 'xrefvalues ', xrefvalues)
        mrefx = (xrefvalues[1] - xrefvalues[0]) / (xrefpath[1] - xrefpath[0])
        trafo = lambda xpathdata: mrefx * (xpathdata - xrefpath[0]) + xrefvalues[0]
        return trafo
    
    def get_real_values(self, xpathdata):
        xnorm = self.xtrafo(xpathdata[:, 0])
        ynorm = self.ytrafo(xpathdata[:, 1])
        return np.array([xnorm, ynorm])

    def get_paths(self):
        path_strings = [(path.getAttribute('id'), path.getAttribute('d')) for path
                        in self.doc.getElementsByTagName('path')]

        xypaths_all = {path_string[0]: self.parse_pathstring(path_string[1]) for path_string in path_strings}

        return xypaths_all    
    

    def parse_pathstring(self, path_string):
        path = parse_path(path_string)
        posxy = []
        for e in path:
            x0 = e.start.real
            y0 = e.start.imag
            x1 = e.end.real
            y1 = e.end.imag
            posxy.append([x0, y0])

        return np.array(posxy)
    
    def create_df(self):
        data = [self.allresults[list(self.allresults)[idx]].transpose() for idx, i in enumerate(self.allresults)]
        self.dfs = [pd.DataFrame(data[idx],columns=[self.xlabel,self.ylabel]) for idx, i in enumerate(data)]
        #for df in self.dfs:
        #    df['t'] = self.create_time_axis(df)
            #df = df[['t','U','I']].copy() #reorder columns does not work
    
    def plot(self):
        '''curve function'''
        #resdict = self.allresults
        #for i, v in resdict.items():
        #    plt.plot(v[0], v[1], label=i)
            
        fig, ax = plt.subplots(1,1)
        for i, df in enumerate(self.dfs):
            df.plot(x=self.xlabel, y=self.ylabel, ax=ax, label=f'curve {i}') 
        # do we want the path in the legend as it was in the previous version?
        #plt.legend()
        plt.xlabel(self.xlabel)
        plt.ylabel(self.ylabel)
        plt.tight_layout()
        plt.show()
    