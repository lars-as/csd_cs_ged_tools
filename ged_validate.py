from arpeggio.cleanpeg import ParserPEG



#CONFIG. VARS
#prefix of output files, change to  "" to overwrite input files
output_file_prefix = "fixed_"
#set to "" to use newline used by current platform instead
prefered_nl = "\n"  




print("Initializing...")

ged_grammar = open("ged.peg", 'r').read()
ged_parser = ParserPEG(ged_grammar, 'gedfile', ws='\t ', skipws=False)

print("Parser initialized...")

print("Output file prefix: {}".format(output_file_prefix))
print("Newline char: {}".format(repr(prefered_nl)))
print("."*80)
print("")

from arpeggio import PTNodeVisitor, visit_parse_tree

import platform

#utility functions
#appends spaces to strings shorter than minimum length l

def pad_r(s, l):
    if len(s) < l:
        return s+' '*(l-len(s))
    return s

def pad_l(s, l):
    if len(s) < l:
        return ' '*(l-len(s))+s
    return s

#AST visitor
#   extracts relevant data from parse tree while discarding
#   formatting
#   errors are reported as they are found

class GED_Visitor(PTNodeVisitor):
    def __init__(self):
        PTNodeVisitor.__init__(self)
        self.nl_win = False
        self.nl_linux = False
        self.nl_mac = False
        self.nl_native = ''
        self.header_line = False
        self.comma_numbers = False
        self.header_sp_missing = False
        
        self.current_line = 0
        
        self.col_names = []
        self.row_names = []
        self.rows = []
        self.error_count = 0
    
    def visit_col_id(self, node, children):
        self.col_names.append(str(node))
        return None

    def visit_g_id(self, node, children):
        self.rows.append([])
        self.row_names.append( str(node) )
        return None

    def visit_number(self, node, children):
        self.rows[ -1 ].append( str(node) )
    
    def visit_header_sp_missing(self, node, children):
        self.header_sp_missing = True
        
    def visit_comma_number(self, node, children):
        self.comma_numbers = True
  
    def visit_newline_linux(self, node, children):
        self.nl_linux = True
    
    def visit_newline_win(self, node, children):
        self.nl_win = True
        
    def visit_newline_mac(self, node, children):
        self.nl_mac = True

    def visit_header_line(self, node, children):
        self.header_line = True

    def error(self, msg):
        print( " ERROR: {}".format(msg) )
        self.error_count += self.error_count+1

    def warning(self, msg):
        print( " warning: {}".format(msg) )

    def validate_newline(self):
        nl_used = [self.nl_win, self.nl_mac, self.nl_linux]
        count= [b for b in nl_used if b]
        if len(count)>1:
            self.error(" Mixed newline character used")

        sys = platform.system()

        eol_found = ""
        if self.nl_win:
            eol_found = "\r\n"
        if self.nl_linux:
            eol_found = '\n'
        if self.nl_mac:
            eol_found = '\r'
        
        eol_expected = ""
        if sys == "Windows":
            eol_expected = "\r\n"
        if sys == "Linux":
            eol_expected = "\n"
        if sys == "Mac":
            eol_expected = "\r"

        self.nl_native = eol_expected if len(eol_expected) else "\n"

        if eol_found and eol_expected and eol_found != eol_expected:
              self.warning("non-native end of line character '{}' found, '{}' expected".format(repr(eol_found), repr(eol_expected)))
        
    def validate_header_line(self):
        if not self.header_line:
            self.warning(" header line containing names of columns not present")
            self.warning(" ///	M0	M1  ... Mn")
        else:
            if self.header_sp_missing:
                self.warning(" space needed between identifier and '///'")

    def validate_rows(self):
        if len(self.rows) == 0:
            self.warning("No data rows present.")
            
        #verify table dimensions
        if self.header_line and self.rows:
            cols = len(self.col_names)
            bad_lines = []
            row_lengths = [ len(r) for r in self.rows ]
            for (x, l) in enumerate(row_lengths):
                if l != cols:
                    bad_lines.append((x, l))

            if bad_lines:
                self.error(" number of columns inconsistent")
                
            if len(bad_lines) < 10:
                for x, l in bad_lines:
                    self.error(" number of entries at line {} is {}, {} expected".format(x+1,l,cols))

            if len(row_lengths) >= 3:
                l0 = row_lengths[0]
                l1 = row_lengths[1]
                l2 = row_lengths[2]
                if l0 != l1 and l1 == l2:
                    self.error(" {} column names found, but {} expected".format(l0, l1))                    

    def validate_number_format(self):
        if self.comma_numbers:
            self.error(""" "," comma found in number literals, "." expected""")
            
    def validate(self):
        self.validate_newline()
        self.validate_header_line()
        self.validate_rows()
        self.validate_number_format()

        return 0 == self.error_count

    def pretty(self, nl=None):
        if nl is None:
            nl = self.nl_native
        if prefered_nl:
            nl = prefered_nl
            
        if self.error_count:
            raise ValueError("Critical errors, could not automatically repair data.")

        s = []

        col_widths = [len(cname) for cname in self.col_names]

        for row in self.rows:
            for x, n in enumerate(row):
                col_widths[x] = max( len(n), col_widths[x] )

        col_widths = [cw+2 for cw in col_widths]

        nc_widths = [len(rw) for rw in self.row_names]
        nc_width = max(nc_widths)
        nc_width = max(nc_width, 5)
        
        if self.header_line:
            s.append( pad_r('///', nc_width) )
            for i, cn in enumerate(self.col_names):
                s.append( pad_l(cn, col_widths[i]) )
        s.append( nl )
        
        for y, row in enumerate(self.rows):
            s.append( pad_r(self.row_names[y], nc_width) )
            for x, n in enumerate(row):
                s.append( pad_l(n, col_widths[x]))
            s.append( nl )
        if len(s):
            s.pop()#remove last newline
        return "".join(s)

def load_file(fname):
    f = open(fname, 'r')
    ged = f.read()
    f.close()
    return ged
        
def visit_ged(ged):
    try:
        res = ged_parser.parse(ged)
        vis = GED_Visitor()
        ged_content = visit_parse_tree(res, vis)
        return vis
    except e:
        print(e)
        print("Sorry, could not parse {}", fname)

def output_filename(fname, prefix="ged_out_"):
    import os.path
    head, tail = os.path.split(fname)
    return os.path.join( head , prefix+tail )

def validate_ged(fname):
    f = open(fname, 'r')
    ged = f.read()
    f.close()
    try:
        res = ged_parser.parse(ged)
        if len(ged) == 0:
            raise ValueError("Error: File empty! {}".format(fname))
        vis = GED_Visitor()
        ged_content = visit_parse_tree(res, vis)
        print("... {}".format(fname))
        vis.validate()
        try:
            p = vis.pretty()
            fnout = output_filename(fname, prefix=output_file_prefix)
            f = open( fnout, 'w+')
            f.write(p)
            f.close()
            print("OUTPUT: ")
            print("    "+ fnout)
        except ValueError as e:
            print(e)
    except Exception as e:
        print(e)
        print("Sorry, could not parse {}", fname)



import sys

for fname in sys.argv[1:]:
    try:
        print()
        validate_ged(fname)
    except e:
        print(e)


if len(sys.argv[1:]) == 0:
    print("Ged repair")
    print("    No input data")
    print("    Pass files as command line arguments")
    print("    Prefix of output files and newline character can be configured")          
    print("    by changing variables at top of .py script.")

##test_folder = "C:\\msys64\\home\\Lars\\CSD_CPP"
##path_testm1 = test_folder + "\\testm1.txt"
##path_testm2 = test_folder + "\\testm2.txt"
##
##def test():
##    validate_ged( path_testm1 )
##    validate_ged( path_testm2 )
##
##vis1 = visit_ged( load_file(path_testm1) )
##vis2 = visit_ged( load_file(path_testm2) )

    
    






