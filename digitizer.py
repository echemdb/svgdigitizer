from svg.path import parse_path
from xml.dom import minidom
import matplotlib.pyplot as plt
import numpy as np

class SvgData():
    def __init__(self, filename, limitlist):
        self.filename = filename
        self.xyrefvalues = np.array(limitlist)

        self.doc = minidom.parse(self.filename)

        self.figpaths = self.get_paths()
        self.xyrefpoints = self.get_refpoints()

        self.xtrafo = self.get_trafo(self.xyrefpoints[:2, 0], self.xyrefvalues[:2])
        self.ytrafo = self.get_trafo(self.xyrefpoints[2:, 1], self.xyrefvalues[2:])
        self.doc.unlink()
        self.get_parsed() ###################### added function
        
    def get_parsed(self): #get_allresults
        self.allresults = {} ################################# added self
        for pathid, pvals in self.figpaths.items():
            self.allresults[pathid] = self.get_real_values(pvals) ############ added self
        #return self.allresults  ####################### removed 

    def plot(self):
        resdict = self.allresults       # self.get_parsed() #------------------- removed and replaced
        for i, v in resdict.items():
            plt.plot(v[0], v[1], label=i)

        plt.legend()
        plt.tight_layout()
        plt.show()
        

    def get_trafo(self, xrefpath, xrefvalues):
        # we assume a rectangular plot
        # xvalue = mrefx * (xpath -xrefpath0 ) + xrefvalue0
        print(xrefpath, xrefvalues)
        mrefx = (xrefvalues[1] - xrefvalues[0]) / (xrefpath[1] - xrefpath[0])
        trafo = lambda xpathdata: mrefx * (xpathdata - xrefpath[0]) + xrefvalues[0]
        return trafo

    def get_real_values(self, xpathdata):
        xnorm = self.xtrafo(xpathdata[:, 0])
        ynorm = self.ytrafo(xpathdata[:, 1])
        return np.array([xnorm, ynorm])

    def guess_xypoints_ordered_keys(self, point_strings):
        # Here we get first the rightmost point on x and then the highest point on y
        # We assume these are the endpoints of our plot
        # Then we choose the point with minimum y distance as the lower end xpoint.
        # This should work in most cases, and for close points with x,y axis meeting e.g. should not matter?!.
        # careful: y is measured from the top in svg file, how great is that!
        rp_keys = list(point_strings.keys())

        if len(point_strings) != 4:
            print("Could not find 4 reference points for the axis." + \
                  "Please Check that you put 4 Ellipsis reference points in your svg figure." +
                  "The found Ellipsis points have these ids: ", point_strings)
            raise Exception


        rp_vals = np.array([point_strings[r] for r in rp_keys])



        #print(rp_vals)
        xmax_ind = np.argmax(rp_vals[:, 0])
        # careful: y is measured from the top in svg file, how great is that!
        ymax_ind = np.argmin(rp_vals[:, 1])

        xmin_ind = np.argsort([ np.linalg.norm(v) for v in np.array(rp_vals) - np.array(rp_vals[xmax_ind])])[1]
        
        ymin_ind = np.setdiff1d([0, 1, 2, 3], [xmax_ind, ymax_ind, xmin_ind]).tolist()
        if len(ymin_ind) > 1:
            print("Could not resolve automatically the axis points.", ymin_ind)
            raise Exception
        else:
            ymin_ind = ymin_ind[0]
        return [rp_keys[l] for l in [xmin_ind, xmax_ind, ymin_ind, ymax_ind]]

    def get_refpoints(self):
        point_strings = self.get_points()
        print("point_strings", point_strings)
        point_strings_ordered_keys = self.guess_xypoints_ordered_keys(point_strings)

        xyrefs = np.array([point_strings[name] for name in point_strings_ordered_keys])

        return xyrefs

    def get_paths(self):
        path_strings = [(path.getAttribute('id'), path.getAttribute('d')) for path
                        in self.doc.getElementsByTagName('path')]

        xypaths_all = {path_string[0]: self.parse_pathstring(path_string[1]) for path_string in path_strings}

        return xypaths_all

    def get_points(self):
        
        point_strings={}
        
        for shape in ['circle', 'ellipse']:
            for path in self.doc.getElementsByTagName(shape):
                point_strings[path.getAttribute('id')] = [float(path.getAttribute('cx')), float(path.getAttribute('cy'))] 
        
        return point_strings

    def parse_pathstring(self, path_string):
        path = parse_path(path_string)
        posxy = []
        for e in path:
            if True:  # isinstance(e, Line):
                x0 = e.start.real
                y0 = e.start.imag
                x1 = e.end.real
                y1 = e.end.imag
                posxy.append([x0, y0])

        return np.array(posxy)
