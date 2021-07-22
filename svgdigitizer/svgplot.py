#*********************************************************************
#  This file is part of svgdigitizer.
#
#        Copyright (C) 2021 Albert Engstfeld
#        Copyright (C) 2021 Johannes Hermann
#        Copyright (C) 2021 Julian Rüth
#        Copyright (C) 2021 Nicolas Hörmann
#
#  svgdigitizer is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  svgdigitizer is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with svgdigitizer. If not, see <https://www.gnu.org/licenses/>.
#*********************************************************************
from svg.path import parse_path
from svgpathtools import Path, Line
from xml.dom import minidom
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path as Pathlib
from functools import cached_property

import re

label_patterns = {
'ref_point': r'^(?P<point>(x|y)\d)\: ?(?P<value>-?\d+\.?\d*) ?(?P<unit>.+)?',
'scale_bar': r'^(?P<axis>x|y)(_scale_bar|sb)\: ?(?P<value>-?\d+\.?\d*) ?(?P<unit>.+)?',
'scaling_factor': r'^(?P<axis>x|y)(_scaling_factor|sf)\: (?P<value>-?\d+\.?\d*)',
'curve': r'^curve: ?(?P<curve_id>.+)',
}

class SVGPlot:
    def __init__(self, filename, xlabel=None, ylabel=None, sampling_interval=None):
        '''filename: should be a valid svg file created according to the documentation'''
        self.filename = filename

        self.xlabel = xlabel or 'x'
        self.ylabel = ylabel or 'y'

        self.doc = minidom.parse(self.filename)
        self.labeled_paths
        self.ref_points, self.real_points = self.get_points()
        
        self.trafo = {}
        for axis in ['x','y']:
            self.trafo[axis] = self.get_trafo(axis)

        self.sampling_interval = sampling_interval

        self.get_parsed()
        self.create_df()
    
    @cached_property
    def transformed_sampling_interval(self):
        factor = 1/((self.trafo['x'](self.sampling_interval)-self.trafo['x'](0))/(self.sampling_interval/1000))
        return factor
    
    def get_points(self):
        '''Creates:
        ref_points: relative values of the spheres/eclipses in the svg file.
        real_points: real values of the points given in the title text of the svg file.'''
        ref_points = {}
        real_points = {}

        for i in self.labeled_paths['ref_point']:
            text, paths, regex_match = i

            ref_point_id = regex_match.group("point")
            real_points[ref_point_id] = float(regex_match.group("value"))

            x_text = float(text.firstChild.getAttribute('x'))
            y_text = float(text.firstChild.getAttribute('y'))

            parsed_path = parse_path(paths[0].getAttribute('d'))

            # always take the point of the path which is further away from text origin
            path_points = []
            path_points.append((parsed_path.point(0).real, parsed_path.point(0).imag))
            path_points.append((parsed_path.point(1).real, parsed_path.point(1).imag))
            if (((path_points[0][0]-x_text)**2 + (path_points[0][1]-y_text)**2)**0.5 >
            ((path_points[1][0]-x_text)**2 + (path_points[1][1]-y_text)**2)**0.5):
                point = 0
            else:
                point = 1

            ref_points[ref_point_id] = {'x': path_points[point][0], 'y': path_points[point][1]}

        return ref_points, real_points

    @cached_property
    def scale_bars(self):
        scale_bars = {}


        for i in self.labeled_paths['scale_bar']:
            text, paths, regex_match = i


            x_text = float(text.firstChild.getAttribute('x'))
            y_text = float(text.firstChild.getAttribute('y'))

            end_points = []
            for path in paths:
                parsed_path = parse_path(path.getAttribute('d'))
            # always take the point of the path which is further away from text origin
                path_points = []
                path_points.append((parsed_path.point(0).real, parsed_path.point(0).imag))
                path_points.append((parsed_path.point(1).real, parsed_path.point(1).imag))
                if (((path_points[0][0]-x_text)**2 + (path_points[0][1]-y_text)**2)**0.5 > 
                ((path_points[1][0]-x_text)**2 + (path_points[1][1]-y_text)**2)**0.5):
                    point = 0
                else:
                    point = 1
                end_points.append(path_points[point])
            
            scale_bars[regex_match.group("axis")] = {}
            if regex_match.group("axis") == 'x':
                scale_bars[regex_match.group("axis")]['ref'] = abs(end_points[1][0] - end_points[0][0] )
            elif regex_match.group("axis") == 'y':
                scale_bars[regex_match.group("axis")]['ref'] = abs(end_points[1][1] - end_points[0][1])
            scale_bars[regex_match.group("axis")]['real'] = float(regex_match.group("value"))

        return scale_bars

    @cached_property
    def scaling_factors(self):
        scaling_factors = {'x': 1, 'y': 1}
        for text in self.doc.getElementsByTagName('text'):

            # parse text content
            text_content = text.firstChild.firstChild.data
            regex_match = re.match(label_patterns['scale_bar'], text_content)

            if regex_match:
                scaling_factors[regex_match.group("axis")] = float(regex_match.group("value"))

        return scaling_factors

    def get_parsed(self):
        '''cuve function'''
        self.allresults = {}
        for pathid, pvals in self.paths.items():
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
            mref = -1/self.scale_bars[axis]['ref'] * self.scale_bars[axis]['real']  / self.scaling_factors[axis] # unclear why we need negative sign: now I know, position of origin !!
            trafo = lambda pathdata: mref * (pathdata - p_ref[f'{axis}1'][axis]) + p_real[f'{axis}1']
        return trafo
    
    def get_real_values(self, xpathdata):
        xnorm = self.trafo['x'](xpathdata[:, 0])
        ynorm = self.trafo['y'](xpathdata[:, 1])
        return np.array([xnorm, ynorm])

    @cached_property
    def labeled_paths(self):
        r"""
        Return all paths which are grouped/label with text elements. Warn if
        unlabeled or ambiguous paths exist.
        """

        labeled_paths = {}

        # determine top level group (layer or svg) by counting groups
        # group with most subgroups is probably the relevant top level
        svg = self.doc.getElementsByTagName('svg')[0]
        group_counts = {}

        for group in svg.getElementsByTagName('g'):
            try:
                group_counts[group.parentNode] += 1
            except KeyError:
                group_counts[group.parentNode] = 1

        sorted_counts = sorted(group_counts.items(), key=lambda item: item[1],reverse=True)
        top_level = sorted_counts[0][0]

        texts = top_level.getElementsByTagName('text')
        for text in texts:
            # group is group for grouped text otherwise it's a layer
            parent = text.parentNode
            paths = parent.getElementsByTagName('path')
            # exclude non-grouped text e.g. scaling_factor
            # and text without grouped paths
            if parent != top_level and len(paths) >= 1:
                match = False
                for key, val in label_patterns.items():
                    regex_match = re.match(val, text.firstChild.firstChild.data)
                    if isinstance(regex_match, re.Match):
                        match = True

                        try:
                            labeled_paths[key].append((text, paths, regex_match))
                        except KeyError:
                            labeled_paths[key] = [(text, paths, regex_match)]

                if not match:
                    print(f"Label not obeying known patterns: \"{text.firstChild.firstChild.data}\"")

                    # warn for ambiguous paths
                    # gives false positive for scale bars
                    #if len(paths) > 1:
                    #    print("""Multiple paths grouped with single text!
                    #          Only first will be taken into account. Please review supplied svg file!""")

                #labeled_paths[text] = paths
        # if more paths (lists) than texts exist it is likely that something is wrong
        if len(labeled_paths) > len([text for text in texts]):
            print("""Unlabeled paths found! Please review supplied svg file!""")

        return labeled_paths

    @cached_property
    def paths(self):
        r"""
        Return the paths that are tracing plots in the SVG, i.e., return all
        the `<path>` tags that are not used for other purposes such as pointing
        to axis labels.
        """

        data_paths = {}
        for i in self.labeled_paths['curve']:
            text, paths, regex_match = i

            if not self.sampling_interval:
                # only consider first path since every curve has a label
                data_paths[paths[0].getAttribute('id')] = self.parse_pathstring(paths[0].getAttribute('d'))
            # sample path if interval set
            elif self.sampling_interval:
                data_paths[paths[0].getAttribute('id')] = self.sample_path(paths[0].getAttribute('d'))

        return data_paths


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


    def sample_path(self, path_string):
        '''samples a path with equidistant x segment by segment'''
        path = Path(path_string)
        xmin, xmax, ymin, ymax = path.bbox()
        x_samples = np.linspace(xmin, xmax, int(abs(xmin - xmax)/self.transformed_sampling_interval))
        points = []
        for segment in path:
            segment_path = Path(segment)
            xmin_segment, xmax_segment, _, _ = segment.bbox()
            segment_points = [[],[]]

            for x in x_samples:
                # only sample the x within the segment
                if x >= xmin_segment and x <= xmax_segment:
                    intersects = Path(Line(complex(x,ymin),complex(x,ymax))).intersect(segment_path)
                    # it is possible that a segment includes both scan directions
                    # which leads to two intersections
                    for i in range(len(intersects)):
                        point = intersects[i][0][1].point(intersects[i][0][0])
                        segment_points[i].append((point.real, point.imag))   

            # second intersection is appended in reverse order!! 
            if len(segment_points[1]) > 0:    
                segment_points[0].extend(segment_points[1][::-1]) 
            # sometimes segments are shorter than sampling interval   
            if len(segment_points[0]) > 0:    
                first_segment_point = (segment.point(0).real, segment.point(0).imag)    

                if (((segment_points[0][-1][0]-first_segment_point[0])**2+(segment_points[0][-1][1]-first_segment_point[1])**2)**0.5 >    
                    ((segment_points[0][0][0]-first_segment_point[0])**2+(segment_points[0][0][1]-first_segment_point[1])**2)**0.5):    
                    points.extend(segment_points[0])    
                else:     
                    points.extend(segment_points[0][::-1]) 

        return np.array(points)  

    def create_df(self):
        data = [self.allresults[list(self.allresults)[idx]].transpose() for idx, i in enumerate(self.allresults)]
        self.dfs = [pd.DataFrame(data[idx],columns=[self.xlabel,self.ylabel]) for idx, i in enumerate(data)]

    def create_csv(self, csvfilename=None):
        r"""
        Creates only a csv file from the first dataframe.
        """
        if csvfilename:
            self.csvfile = Pathlib(csvfilename).with_suffix('.csv')
        else:
            self.csvfile = Pathlib(self.filename).with_suffix('.csv')
        self.dfs[0].to_csv(self.csvfile, index=False)
    
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
    
