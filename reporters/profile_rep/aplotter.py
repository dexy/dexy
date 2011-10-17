#-----------------------------------------------
#aplotter.py - ascii art function plotter
#Copyright (c) 2006, Imri Goldberg
#All rights reserved.
# http://www.algorithm.co.il/blogs/ascii-plotter/
#
#Redistribution and use in source and binary forms,
#with or without modification, are permitted provided
#that the following conditions are met:
#
#    * Redistributions of source code must retain the
#        above copyright notice, this list of conditions
#        and the following disclaimer.
#    * Redistributions in binary form must reproduce the
#        above copyright notice, this list of conditions
#        and the following disclaimer in the documentation
#        and/or other materials provided with the distribution.
#    * Neither the name of the <ORGANIZATION> nor the names of
#        its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
#LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#-----------------------------------------------

import math


EPSILON = 0.000001

def transposed(mat):
    result = []
    for i in xrange(len(mat[0])):
        result.append([x[i] for x in mat])
    return result

def y_reversed(mat):    
    result = []
    for i in range(len(mat)):
        result.append(list(reversed(mat[i])))
    return result

def sign(x):
    if 0<x:
        return 1
    if 0 == x:
        return 0
    return -1

class Plotter(object):

    class PlotData(object):
        def __init__(self, x_size, y_size, min_x, max_x, min_y, max_y, x_mod, y_mod):
            self.x_size = x_size
            self.y_size = y_size
            self.min_x = min_x
            self.max_x = max_x
            self.min_y = min_y
            self.max_y = max_y
            self.x_mod = x_mod
            self.y_mod = y_mod

            self.x_step = float(max_x - min_x)/float(self.x_size)
            self.y_step = float(max_y - min_y)/float(self.y_size)
            self.inv_x_step = 1/self.x_step
            self.inv_y_step = 1/self.y_step

            self.ratio = self.y_step / self.x_step
        def __repr__(self):
            s = "size: %s, bl: %s, tr: %s, step: %s" % ((self.x_size, self.y_size), (self.min_x, self.min_y), (self.max_x, self.max_y),
                                                         (self.x_step, self.y_step))
            return s
    
    def __init__(self, **kwargs):

        self.x_size = kwargs.get("x_size", 80)
        self.y_size = kwargs.get("y_size", 20)

        self.will_draw_axes = kwargs.get("draw_axes", True)

        self.new_line = kwargs.get("newline", "\n")

        self.dot = kwargs.get("dot", "*")

        self.plot_slope = kwargs.get("plot_slope", True)

        self.x_margin = kwargs.get("x_margin", 0.05)
        self.y_margin = kwargs.get("y_margin", 0.1)

        self.will_plot_labels = kwargs.get("plot_labels", True)

    @staticmethod
    def get_symbol_by_slope(slope, default_symbol):
        draw_symbol = default_symbol
        if slope > math.tan(3*math.pi/8):
            draw_symbol = "|"
        elif slope > math.tan(math.pi/8) and slope < math.tan(3*math.pi/8):
            draw_symbol = "/"
        elif abs(slope) < math.tan(math.pi/8):
            draw_symbol = "-"
        elif slope < math.tan(-math.pi/8) and slope > math.tan(-3*math.pi/8):
            draw_symbol = "\\"
        elif slope < math.tan(-3*math.pi/8):
            draw_symbol = "|"
        return draw_symbol    


    def plot_labels(self, output_buffer, plot_data):
        if plot_data.y_size < 2:
            return

        margin_factor = 1

        do_plot_x_label = True
        do_plot_y_label = True

        x_str = "%+g"
        if plot_data.x_size < 16:
            do_plot_x_label = False
        elif plot_data.x_size < 23:
            x_str = "%+.2g" 

        y_str = "%+g"    
        if plot_data.x_size < 8:
            do_plot_y_label = False
        elif plot_data.x_size < 11:
            y_str = "%+.2g"
            
        act_min_x = (plot_data.min_x + plot_data.x_mod*margin_factor)
        act_max_x = (plot_data.max_x - plot_data.x_mod*margin_factor)
        act_min_y = (plot_data.min_y + plot_data.y_mod*margin_factor)
        act_max_y = (plot_data.max_y - plot_data.y_mod*margin_factor)

        if abs(act_min_x) < 1:
            min_x_str = "%+.2g" % act_min_x
        else:
            min_x_str = x_str % act_min_x

        if abs(act_max_x) < 1:
            max_x_str = "%+.2g" % act_max_x
        else:
            max_x_str = x_str % act_max_x
        
        if abs(act_min_y) < 1:
            min_y_str = "%+.2g" % act_min_y
        else:
            min_y_str = y_str % act_min_y

        if abs(act_max_y) < 1:
            max_y_str = "%+.2g" % act_max_y
        else:
            max_y_str = y_str % act_max_y
                         
        min_x_coord = self.get_coord(act_min_x,plot_data.min_x,plot_data.x_step)
        max_x_coord = self.get_coord(act_max_x,plot_data.min_x,plot_data.x_step)
        min_y_coord = self.get_coord(act_min_y,plot_data.min_y,plot_data.y_step)
        max_y_coord = self.get_coord(act_max_y,plot_data.min_y,plot_data.y_step)
                                 

        #print plot_data
        
        y_zero_coord = self.get_coord(0, plot_data.min_y, plot_data.y_step)

        if plot_data.min_x < 0 and plot_data.max_x > 0:
             x_zero_coord = self.get_coord(0, plot_data.min_x, plot_data.x_step)
        else:
             pass

        try:
            output_buffer[x_zero_coord][min_y_coord] = "+"
            output_buffer[x_zero_coord][max_y_coord] = "+"
            output_buffer[min_x_coord][y_zero_coord] = "+"
            output_buffer[max_x_coord][y_zero_coord] = "+"
        except:
             pass

        if do_plot_x_label:

            for i,c in enumerate(min_x_str):
                output_buffer[min_x_coord+i][y_zero_coord-1] = c
            for i,c in enumerate(max_x_str):
                output_buffer[max_x_coord+i-len(max_x_str)][y_zero_coord-1] = c

        if do_plot_y_label:

            for i,c in enumerate(max_y_str):
                output_buffer[x_zero_coord+i][max_y_coord] = c
            for i,c in enumerate(min_y_str):
                output_buffer[x_zero_coord+i][min_y_coord] = c
            

        
        
    
    def plot_data(self, xy_seq, output_buffer, plot_data):
        if self.plot_slope:
            xy_seq = list(xy_seq)
            #sort according to the x coord
            xy_seq.sort(key = lambda c: c[0])
            prev_p = xy_seq[0]
            e_xy_seq = enumerate(xy_seq)
            e_xy_seq.next()
            for i,(x,y) in e_xy_seq:
                draw_symbol = self.dot
                line_drawn = self.plot_line(prev_p, (x,y), output_buffer, plot_data)
                prev_p = (x,y)
                if not line_drawn:
                    if i > 0 and i < len(xy_seq)-1:
                        px,py = xy_seq[i-1]
                        nx,ny = xy_seq[i+1]

                        if abs(nx-px) > EPSILON:
                            slope = (1.0/plot_data.ratio)*(ny-py)/(nx-px)
                            draw_symbol = self.get_symbol_by_slope(slope, draw_symbol)
                    if x < plot_data.min_x or x >= plot_data.max_x or y < plot_data.min_y or y >= plot_data.max_y:
                        continue
                    
                    x_coord = self.get_coord(x, plot_data.min_x, plot_data.x_step)
                    y_coord = self.get_coord(y, plot_data.min_y, plot_data.y_step)            
                    if x_coord >= 0 and x_coord < len(output_buffer) and y_coord >= 0 and y_coord < len(output_buffer[0]):
                        if self.draw_axes:
                            if y_coord == self.get_coord(0, plot_data.min_y, plot_data.y_step) and draw_symbol == "-":
                                draw_symbol = "="
                        output_buffer[x_coord][y_coord] = draw_symbol
        else:
            for x,y in xy_seq:
                if x < plot_data.min_x or x >= plot_data.max_x or y < plot_data.min_y or y >= plot_data.max_y:
                    continue
                x_coord = self.get_coord(x, plot_data.min_x, plot_data.x_step)
                y_coord = self.get_coord(y, plot_data.min_y, plot_data.y_step)
                if x_coord >= 0 and x_coord < len(output_buffer) and y_coord > 0 and y_coord < len(output_buffer[0]):
                    output_buffer[x_coord][y_coord] = self.dot


    def plot_line(self, start, end, output_buffer, plot_data):

        start_coord = self.get_coord(start[0], plot_data.min_x, plot_data.x_step), self.get_coord(start[1], plot_data.min_y, plot_data.y_step)
        end_coord = self.get_coord(end[0], plot_data.min_x, plot_data.x_step), self.get_coord(end[1], plot_data.min_y, plot_data.y_step)

        x0,y0 = start_coord
        x1,y1 = end_coord
        if (x0,y0) == (x1,y1):
            return True    
        
        clipped_line = clip_line(start, end, (plot_data.min_x, plot_data.min_y), (plot_data.max_x, plot_data.max_y))
        if clipped_line != None:
            start,end = clipped_line
        else:
            return False
        start_coord = self.get_coord(start[0], plot_data.min_x, plot_data.x_step), self.get_coord(start[1], plot_data.min_y, plot_data.y_step)
        end_coord = self.get_coord(end[0], plot_data.min_x, plot_data.x_step), self.get_coord(end[1], plot_data.min_y, plot_data.y_step)

        x0,y0 = start_coord
        x1,y1 = end_coord
        if (x0,y0) == (x1,y1):
            return True
        x_zero_coord = self.get_coord(0, plot_data.min_x, plot_data.x_step)
        y_zero_coord = self.get_coord(0, plot_data.min_y, plot_data.y_step)   

        if start[0]-end[0] == 0:
            draw_symbol = "|"
        else:
            slope = (1.0/plot_data.ratio)*(end[1]-start[1])/(end[0]-start[0])
            draw_symbol = self.get_symbol_by_slope(slope, self.dot)
        try:

            delta = x1-x0, y1-y0
            if abs(delta[0])>abs(delta[1]):
                s = sign(delta[0])
                slope = float(delta[1])/delta[0]
                for i in range(0,abs(int(delta[0]))):
                    cur_draw_symbol = draw_symbol
                    x = i*s
                    cur_y = int(y0+slope*x)
                    if self.draw_axes and cur_y == y_zero_coord and draw_symbol == "-":
                        cur_draw_symbol = "="
                    output_buffer[x0+x][cur_y] = cur_draw_symbol
                
                
            else:
                s = sign(delta[1])
                slope = float(delta[0])/delta[1]
                for i in range(0,abs(int(delta[1]))):
                    y = i*s
                    cur_draw_symbol = draw_symbol
                    cur_y = y0+y
                    if self.draw_axes and cur_y == y_zero_coord and draw_symbol == "-":
                        cur_draw_symbol = "="
                    output_buffer[int(x0+slope*y)][cur_y] = cur_draw_symbol
        except:
            print start, end
            print start_coord, end_coord
            print plot_data
            raise

        return False            
        
        
    def plot_single(self, seq, min_x = None, max_x = None, min_y = None, max_y = None):
        return self.plot_double(range(len(seq)),seq, min_x, max_x, min_y, max_y)
        



    def plot_double(self, x_seq, y_seq, min_x = None, max_x = None, min_y = None, max_y = None):
        if min_x == None:
            min_x = min(x_seq)
        if max_x == None:
            max_x = max(x_seq)
        if min_y == None:
            min_y = min(y_seq)
        if max_y == None:
            max_y = max(y_seq)

        if max_y == min_y:
            max_y += 1

        x_mod = (max_x-min_x)*self.x_margin
        y_mod = (max_y-min_y)*self.y_margin
        min_x-=x_mod
        max_x+=x_mod
        min_y-=y_mod
        max_y+=y_mod


        plot_data = self.PlotData(self.x_size, self.y_size, min_x, max_x, min_y, max_y, x_mod, y_mod)

        output_buffer = [[" "]*self.y_size for i in range(self.x_size)]

        if self.will_draw_axes:
            self.draw_axes(output_buffer, plot_data)

        self.plot_data(zip(x_seq, y_seq), output_buffer, plot_data)

        if self.will_plot_labels:
            self.plot_labels(output_buffer, plot_data)

        trans_result = transposed(y_reversed(output_buffer))

        result = self.new_line.join(["".join(row) for row in trans_result])
        return result

    def draw_axes(self, output_buffer, plot_data):
        
        
        draw_x = False
        draw_y = False

        if plot_data.min_x <= 0 and plot_data.max_x > 0:
            draw_y = True
            zero_x = self.get_coord(0, plot_data.min_x, plot_data.x_step)
            for y in xrange(plot_data.y_size):
                output_buffer[zero_x][y] = "|"
                
        if plot_data.min_y <= 0 and plot_data.max_y > 0:
            draw_x = True
            zero_y = self.get_coord(0, plot_data.min_y, plot_data.y_step)    
            for x in xrange(plot_data.x_size):
                output_buffer[x][zero_y] = "-"

        if draw_x and draw_y:
            output_buffer[zero_x][zero_y] = "+"
        
        
    @staticmethod
    def get_coord(val, min, step):
        result = int((val - min)/step)
        return result

def clip_line(line_pt_1, line_pt_2, rect_bottom_left, rect_top_right):
    ts = [0.0,1.0]
    if line_pt_1[0] == line_pt_2[0]:
        return ((line_pt_1[0], max(min(line_pt_1[1], line_pt_2[1]), rect_bottom_left[1])),
                (line_pt_1[0], min(max(line_pt_1[1], line_pt_2[1]), rect_top_right[1])))
    if line_pt_1[1] == line_pt_2[1]:
        return ((max(min(line_pt_1[0], line_pt_2[0]), rect_bottom_left[0]), line_pt_1[1]),
                (min(max(line_pt_1[0], line_pt_2[0]), rect_top_right[0]), line_pt_1[1]))

    if ((rect_bottom_left[0] <= line_pt_1[0] and line_pt_1[0] < rect_top_right[0]) and
        (rect_bottom_left[1] <= line_pt_1[1] and line_pt_1[1] < rect_top_right[1]) and
        (rect_bottom_left[0] <= line_pt_2[0] and line_pt_2[0] < rect_top_right[0]) and
        (rect_bottom_left[1] <= line_pt_2[1] and line_pt_2[1] < rect_top_right[1])):
        return line_pt_1, line_pt_2

    ts.append( float(rect_bottom_left[0]-line_pt_1[0])/(line_pt_2[0]-line_pt_1[0]) )
    ts.append( float(rect_top_right[0]-line_pt_1[0])/(line_pt_2[0]-line_pt_1[0]) )
    ts.append( float(rect_bottom_left[1]-line_pt_1[1])/(line_pt_2[1]-line_pt_1[1]) )
    ts.append( float(rect_top_right[1]-line_pt_1[1])/(line_pt_2[1]-line_pt_1[1]) )
    
    ts.sort()
    if ts[2] < 0 or ts[2] >= 1 or ts[3] < 0 or ts[2]>= 1:
        return None
    result = [(pt_1 + t*(pt_2-pt_1)) for t in (ts[2],ts[3]) for (pt_1, pt_2) in zip(line_pt_1, line_pt_2)]
    return (result[0],result[1]), (result[2], result[3])
    


def plot(*args,**flags):
    limit_flags_names = set(["min_x","min_y","max_x","max_y"])
    limit_flags = dict([(n,flags[n]) for n in limit_flags_names & set(flags)])
    settting_flags = dict([(n,flags[n]) for n in set(flags) - limit_flags_names])
    
    if len(args) == 1:
        p = Plotter(**settting_flags)
        return p.plot_single(args[0],**limit_flags)
    elif len(args) == 2:
        p = Plotter(**settting_flags)
        return p.plot_double(args[0],args[1],**limit_flags)
    else:
        raise NotImplementedError("can't draw multiple graphs yet")
    
__all__ = ["Plotter","plot"]

