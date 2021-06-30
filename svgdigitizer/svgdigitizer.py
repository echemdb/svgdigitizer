from svg.path import parse_path
from xml.dom import minidom
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from functools import cached_property

import re

ref_point_regex_str = r'^(?P<point>(x|y)\d)\: ?(?P<value>\d+\.?\d*) ?(?P<unit>.+)?'
scalebar_regex_str = r'^(?P<axis>x|y)(_scalebar|sb)\: ?(?P<value>\d+\.?\d*) ?(?P<unit>.+)?'
scaling_factor_regex_str = r'^(?P<axis>x|y)(_scaling_factor|sf)\: (?P<value>\d+\.?\d*)'

class SvgData:
    def __init__(self, filename, xlabel=None, ylabel=None):
        '''filename: should be a valid svg file created according to the documentation'''
        self.filename = filename
        
        self.xlabel = xlabel or 'x'
        self.ylabel = ylabel or 'y'
        
        self.doc = minidom.parse(self.filename)

        self.figpaths = self.get_paths()
        
        self.ref_points, self.real_points = self.get_points()
        

        self.trafo = {}
        for axis in ['x','y']:
            self.trafo[axis] = self.get_trafo(axis)

        
        self.doc.unlink()
        self.get_parsed()
        self.create_df()
        
    
    def get_points(self):
        '''Creates:
        ref_points: relative values of the spheres/eclipses in the svg file.
        real_points: real values of the points given in the title text of the svg file.'''
        ref_points = {}
        real_points = {}


        for text in self.doc.getElementsByTagName('text'):

            # parse text content

            text_content = text.firstChild.firstChild.data
            regex_match =re.match(ref_point_regex_str, text_content)
            if regex_match:
                ref_point_id = regex_match.group("point")
                real_points[ref_point_id] = float(regex_match.group("value"))
                ref_points[ref_point_id] = {'x': float(text.firstChild.getAttribute('x')), 'y': float(text.firstChild.getAttribute('y'))}

        
        print('Ref points: ', ref_points)
        print('point values: ',real_points)
        return ref_points, real_points
        
    @cached_property
    def scalebars(self):
        scalebars = {}

        for path in self.doc.getElementsByTagName('path'):
            try:
                title = path.getElementsByTagName('title')[0].firstChild.data
            except IndexError: # skip without title text
                continue

            regex_match = re.match(scalebar_regex_str, title)
            if regex_match:
                parsed_path = parse_path(path.getAttribute('d'))
                scalebars[regex_match.group("axis")] = {}
                if regex_match.group("axis") == 'x':
                    scalebars[regex_match.group("axis")]['ref'] = abs(parsed_path.point(1).real - parsed_path.point(0).real)
                elif regex_match.group("axis") == 'y':
                    scalebars[regex_match.group("axis")]['ref'] = abs(parsed_path.point(1).imag - parsed_path.point(0).imag)
                scalebars[regex_match.group("axis")]['real'] = float(regex_match.group("value"))

        return scalebars

    @cached_property
    def scaling_factors(self):
        scaling_factors = {'x': 1, 'y': 1}
        for text in self.doc.getElementsByTagName('text'):

            # parse text content
            text_content = text.firstChild.firstChild.data
            regex_match = re.match(scaling_factor_regex_str, text_content)

            if regex_match:
                scaling_factors[regex_match.group("axis")] = float(regex_match.group("value"))
        return scaling_factors

    def get_parsed(self):
        '''cuve function'''
        self.allresults = {}
        for pathid, pvals in self.figpaths.items():
            self.allresults[pathid] = self.get_real_values(pvals)
    

    def get_trafo(self, axis):
        # we assume a rectangular plot
        # value = mref * (path - refpath0 ) + refvalue0
        #print('refpath ', refpath, 'refvalues ', refvalues)
        p_real = self.real_points
        p_ref = self.ref_points
        try:
            mref = (p_real[f'{axis}2'] - p_real[f'{axis}1']) / (p_ref[f'{axis}2'][axis] - p_ref[f'{axis}1'][axis]) / self.scaling_factors[axis]
            trafo = lambda pathdata: mref * (pathdata - p_ref[f'{axis}1'][axis]) + p_real[f'{axis}1']
        except KeyError:
            mref = -1/self.scalebars[axis]['ref'] * self.scalebars[axis]['real']  / self.scaling_factors[axis] # unclear why we need negative sign: now I know, position of origin !!
            trafo = lambda pathdata: mref * (pathdata - p_ref[f'{axis}1'][axis]) + p_real[f'{axis}1']
        return trafo
    
    def get_real_values(self, xpathdata):
        xnorm = self.trafo['x'](xpathdata[:, 0])
        ynorm = self.trafo['y'](xpathdata[:, 1])
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
            if df.shape[0] > 2: # do not plot scalebars, which are only 2 points
                df.plot(x=self.xlabel, y=self.ylabel, ax=ax, label=f'curve {i}') 
        # do we want the path in the legend as it was in the previous version?
        #plt.legend()
        plt.xlabel(self.xlabel)
        plt.ylabel(self.ylabel)
        plt.tight_layout()
        plt.show()
    
