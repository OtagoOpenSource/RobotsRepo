# File: SimpleEditor.py
# Created: 9th May, 2013
# Creator: Brendan McCane
# License: not sure yet, some open source license

import Tkinter
import ScrolledText
#import update_mark
import tkFileDialog
import tkSimpleDialog
import subprocess
import tkMessageBox
import re
import webbrowser
import keyword #SH
from string import ascii_letters, digits, punctuation, join #SH
import os
import sys
import tempfile

# container class for tokens to be highlighted
import Highlighter

# container class for function help
import FunctionExplainer

# a global singleton list of windows
AllWindows = []

class SimpleEditor:
    """
    A simple editor for NQC code.
    """

    # define tags for keywords, identifiers, numbers
    tags = {'keyword': '#960', 'int': '#c00', 'identifier': '#960', 'function': '#009', 'macro': '#a0f', 'constant': '#a0f', 'struct': '#900', 'comment': '#090'}

    def __init__(self, parent, compiler='./nbc'):
        self.parent = parent
        parent.title("Lego Editor")
        self.compiler = compiler
        # this frame contains the in-app clickable buttons
        self.menuFrame = Tkinter.Frame(parent, height=24, width=80)
        self.menuFrame.pack(side=Tkinter.TOP)

        #the pane which holds the text and the compiler
        self.pWindow = Tkinter.PanedWindow(parent, orient=Tkinter.VERTICAL, handlesize=5, borderwidth=0, bg="#000", showhandle=True)
        self.pWindow.pack(side=Tkinter.BOTTOM, fill=Tkinter.BOTH, expand=1)

        self.textFrame = Tkinter.Frame(parent)
        self.textWidget = ScrolledText.ScrolledText(self.textFrame, width=80, height=40, undo=True)
        self.textWidget.pack(fill=Tkinter.BOTH, padx=2, pady=2)

        #adds textWidget to the top of the pane
        self.pWindow.add(self.textFrame)

        # this is for the output from the compiler
        self.compilerFrame = Tkinter.Frame(parent)
        self.compilerWidget = ScrolledText.ScrolledText(self.compilerFrame, width=80, height=20)
        self.compilerWidget.pack(fill=Tkinter.BOTH, padx=2, pady=2)
        self.compilerWidget.bind('<ButtonRelease>', self.find_line_num)
        self.pWindow.add(self.compilerFrame)

        # used to keep track of the lines where errors are on
        self.error_lines = []
        self.error_pos = -1

        #Syntax Highlighting: Should be put into a separate module
        #define a tag for highlighting the current line
        self.textWidget.tag_configure("current_line", background="#e8e800")
        self.config_tags()
        self.characters = ascii_letters + digits + punctuation
        self.textWidget.bind('<Key>', self.key_press)

        # set up the menus
        #set up clickable buttons
        buttonNames = ["New", "Open", "Save", "Check Syntax",
                "Compile", "Prev Err", "Next Err"]
        buttonCommands = [self.new_command, self.open_command, self.save_command, self.check_syntax, self.compile_upload, self.prev_error, self.next_error]
        for buttonName, buttonCommand in zip(buttonNames, buttonCommands):
            self.Button = Tkinter.Button(self.menuFrame, text=buttonName, 
                    command=buttonCommand)
            if buttonName in ["Check Syntax", "Prev"]: #space the buttons
                self.Button.pack(side=Tkinter.LEFT, padx=(20, 0))
            else:
                self.Button.pack(side=Tkinter.LEFT)
        self.lineLabel = Tkinter.Label(self.menuFrame, text="Line: 1.0", highlightthickness=1, highlightbackground="#000000")
        self.lineLabel.pack(side=Tkinter.LEFT)
        self.textWidget.bind('<KeyRelease>', self.update_linenum_label)
        self.textWidget.bind('<ButtonRelease>', self.update_linenum_label)
        
        # todo - add shortcuts and possible shortcut icons
        self.menuBar = Tkinter.Menu(parent, tearoff=0)
        self.fileMenu = Tkinter.Menu(self.menuBar, tearoff=0)
        self.fileMenu.add_command(label="New", underline=1, command=self.new_command, accelerator="Ctrl+N")
        self.fileMenu.add_command(label="Open", command=self.open_command, accelerator="Ctrl+O")
        self.fileMenu.add_command(label="Save", command=self.save_command, accelerator="Ctrl+S")
        self.fileMenu.add_command(label="Save As", command=self.saveas_command, accelerator="Ctrl+Shift+S")
        self.fileMenu.add_command(label="Close", command=self.close_command)
        self.fileMenu.add_command(label="Quit", command=self.quit_command, accelerator="Ctrl+Q")
        self.parent.createcommand('exit', self.quit_command)
        self.menuBar.add_cascade(label="File", menu=self.fileMenu)

        self.editMenu = Tkinter.Menu(parent, tearoff=0)
        self.editMenu.add_command(label="Undo", command=self.undo_command, accelerator="Ctrl+Z")
        self.editMenu.add_command(label="Redo", command=self.redo_command, accelerator="Ctrl+Y")
        self.editMenu.add_command(label="Font Size...", command=self.font_size_command)
        self.menuBar.add_cascade(label="Edit", menu=self.editMenu)

        self.commandMenu = Tkinter.Menu(self.menuBar, tearoff=0)
        self.commandMenu.add_command(label="Check Syntax", 
                command=self.check_syntax)
        self.commandMenu.add_command(label="Compile and Upload", 
                command = self.compile_upload)
        self.commandMenu.add_command(label="Next Error", 
                command = self.next_error)
        self.commandMenu.add_command(label="Previous Error", 
                command = self.prev_error)
        self.menuBar.add_cascade(label="Compile", menu=self.commandMenu)

        self.helpMenu = Tkinter.Menu(self.menuBar, tearoff=0)
        self.helpMenu.add_command(label="Explain selected function...", command=self.function_explain_command, accelerator="Ctrl+Shift+H")
        self.helpMenu.add_command(label="NXC Help (opens webpage)",
                                     command=self.open_API)
        self.menuBar.add_cascade(label="Help", menu=self.helpMenu);

        parent.config(menu=self.menuBar)

        # initialise the file associated with this window as ''
        self.filename = ''
        self.textWidget.edit_modified(False)

        # timer variable to only highlight when user stops typing
        self.highlight_timeout = None

        # add the new object to the list of all windows.
        AllWindows.append(self)

    def new_command(self):
        """
        Create a blank new text window
        """
        root = Tkinter.Tk()
        new_editor = SimpleEditor(root, self.compiler)
        root.mainloop()
        return new_editor

    def open_new_command(self):
        """
        Open a new file in a new window.
        """
        root = Tkinter.Tk()
        new_editor = SimpleEditor(root, self.compiler)
        new_editor.open_command()
        root.mainloop()
        return new_editor

    def open_command(self):
        """
        Open an existing file in the current window via user input
        """
        if self.filename == '' and not self.textWidget.edit_modified():
            self.filename = tkFileDialog.askopenfilename()
            if self.filename != '':
              self._open_command(self.filename)
        else:
            editor = self.open_new_command()

    def _open_command(self, filename):
        """
        Actually open an existing file in the current window
        """
        if filename == "":
          print "open_command error: blank filename"
        file = open(self.filename, "rU")
        contents = file.read()
        self.textWidget.insert(Tkinter.END, contents)
        file.close()
        self.textWidget.edit_modified(False)
        self.rehighlight()
        dirs = self.filename.split('/')
        self.parent.title(dirs[-1])

    def save_command(self):
        """
        Save the current contents to the current file.
        """
        if self.filename=='' or self.filename==():
            return self.saveas_command()
        else:
            file = open(self.filename, "w")
            contents = self.textWidget.get("1.0", Tkinter.END)[:-1]
            file.write(contents)
            file.close()
            self.rehighlight()
            return True

    def saveas_command(self):
        """
        Save the current contents to an as yet unnamed file
        """
        self.filename = tkFileDialog.asksaveasfilename()
        # sometimes it returns a tuple
        if self.filename != '' and self.filename != ():
            print self.filename
            file = open(self.filename, "w")
            contents = self.textWidget.get("1.0", Tkinter.END)[:-1]
            file.write(contents)
            file.close()
            self.textWidget.edit_modified(False)
            self.rehighlight()
            dirs = self.filename.split('/')
            self.parent.title(dirs[-1])
            return True
        else:
            return False

    def really_quit(self):
        del AllWindows[AllWindows.index(self)]
        print AllWindows
        self.parent.destroy()
        return True

    def close_command(self):
        """
        Close this file. Should check to see if saving is needed.
        """
        if self.textWidget.edit_modified():
            if self.filename == '' or self.filename == ():
                fname = "Unsaved File"
            else:
                fname = self.filename
            if tkMessageBox.askyesno("Unsaved File",
                                     "File: " + fname + 
                                     " hasn't been saved." + 
                                     " Quit anyway?"):
                print "Trying to quit"
                return self.really_quit()
            else:
                print "Not trying to quit"
                return False
        else:
            print "Quitting this way"
            return self.really_quit()

    def quit_command(self):
        """
        Quit the whole application. This is more difficult. The
        singleton global AllWindows contains all the various windows
        created. This just cycles through them and closes each of
        them.
        """
        while len(AllWindows)>0:
            window = AllWindows[0]
            print "quit" + str(window)
            if not window.close_command():
                print "Window close false"
                return
            else:
                print "Huh?"

    def check_or_compile(self, upload):
        """
        Check the syntax of current contents by calling the NBC
        compiler. Needs to create a sub window for the output of the
        compiler and in the case of errors parse the output and move
        the cursor to the appropriate line.
        """
        self.compilerWidget.delete("1.0", Tkinter.END)
        if not upload:
            self.compilerWidget.insert(Tkinter.END, 'Checking syntax\n')
        else:
            self.compilerWidget.insert(Tkinter.END, 'Compiling and uploading\n')

        if self.textWidget.edit_modified():
            self.save_command()
        try:
            cfile = tempfile.NamedTemporaryFile()
            nfile = tempfile.NamedTemporaryFile()
            if not upload:
                compile = subprocess.check_call([self.compiler, 
                                                 self.filename, 
                                                 '-O={}.rxe'.format(self.filename)],
                                                stderr=cfile, stdout=nfile) 
            else:
                compile = subprocess.check_call([self.compiler, '-d', 
                                                 self.filename],
                                                stderr=cfile, stdout=nfile) 

            self.compilerWidget.insert(Tkinter.END, "Hooray, compile successful")
        except subprocess.CalledProcessError as e:
            self.compilerWidget.insert(Tkinter.END, str(e))
            cfile.seek(0)
            nfile.seek(0)
            lines = cfile.readlines()
            lines = [x for x in lines if not x.startswith('# Status')]
            self.error_lines = []
            self.error_pos = -1
            for line in lines:
                m = re.search('(line) ([0-9]+)', line)
                if m is not None:
                    if m.lastindex==2:
                        self.error_lines += [int(m.group(2))]
            output = ''.join(lines)
            # self.compilerWidget.delete("1.0", Tkinter.END)
            self.compilerWidget.insert(Tkinter.END, output)
        except Exception as e:
            self.compilerWidget.insert(Tkinter.END, str(e))
            print 'here'
        finally:
            cfile.close()
            nfile.close()
        #os.remove('.fhtyzbg.out')
        #os.remove('.flondgy.out')

    def check_syntax(self):
        self.check_or_compile(False)

    def compile_upload(self):
        """
        Compile and upload the program to an actual lego brick. Again
        using the NBC compiler.
        """
        self.check_or_compile(True)

    def highlight_current_line(self):
        self.textWidget.tag_remove("current_line", 1.0, "end")
        self.textWidget.tag_add("current_line", "insert linestart", "insert lineend")

    # XXX go to "line + 1" since compiler starts at '0' and editor starts at '1'
    def goto_line(self, linenum):
        linenum += 1
        index = "%d.%d" % (linenum, 0)
        self.textWidget.mark_set("insert", index)
        self.textWidget.see(index)
        self.highlight_current_line()
        self.rehighlight()
        self.update_linenum_label(None)
        
    def next_error(self):
        if len(self.error_lines) == 0: return
        self.error_pos += 1
        self.error_pos %= len(self.error_lines)
        self.goto_line(self.error_lines[self.error_pos])

    def prev_error(self):
        if len(self.error_lines) == 0: return
        self.error_pos -= 1
        if self.error_pos < 0: self.error_pos = len(self.error_lines)-1
        self.goto_line(self.error_lines[self.error_pos])

    def undo_command(self):
        try:
            self.textWidget.edit_undo()
            self.rehighlight()
        except:
            pass

    def redo_command(self):
        try:
            self.textWidget.edit_redo()
            self.rehighlight()
        except:
            pass

    def font_size_command(self):
        newFontSize = tkSimpleDialog.askinteger("Set font size", "What font size would you like? (6-72).", minvalue=6, maxvalue=72)
        if newFontSize != None:
            self.textWidget.configure(font=('courier', newFontSize, 'normal'))

    # Explains selected text via pop-up
    def function_explain_command(self):
        selectedFunction = self.textWidget.selection_get()
        functionExplainer = FunctionExplainer.FunctionExplainer()
        if selectedFunction in functionExplainer.knownFunctions:
            helpfulInformation = functionExplainer.knownFunctions[selectedFunction]
            for additionalInfo in functionExplainer.knownParameters:
                if additionalInfo in helpfulInformation:
                    helpfulInformation += '\n' + functionExplainer.knownParameters[additionalInfo]
            tkMessageBox.showinfo("Help for \"" + selectedFunction + "\"", helpfulInformation)
        else:
            tkMessageBox.showwarning("Help for \"" + selectedFunction + "\"", "I don't know anything about that. Sorry.")

    def open_API(self):
        """
        Eventually pop up some form of useful information on functions that
        NXC uses
        """
        webbrowser.open("http://bricxcc.sourceforge.net/nbc/nxcdoc/nxcapi/index.html")
        api_test = subprocess.check_output([self.compiler + ' -api', 
                                        self.filename, 
                                        '-O={}.rxe'.format(self.filename)],
                                       stderr=subprocess.STDOUT) 
        print api_test

    def update_linenum_label(self, event):
      self.lineLabel.config(text='Line: '+self.textWidget.index('insert'))

    # Assumes compiler errors occupy four lines, moves to appropriate error
    # line when user clicks in the compiler output window
    def find_line_num(self, event):
        mouseIndex = "@%d,%d" % (event.x, event.y)
        index = self.compilerWidget.index(mouseIndex)
        linenum = int((int(float(index))-1)/4)
        if linenum<len(self.error_lines):
            self.goto_line(self.error_lines[linenum])

### Begin Syntax Highlighting
    def config_tags(self):
        for tag, val in self.tags.items():
            self.textWidget.tag_config(tag, foreground=val)

    def remove_tags(self, start, end):
        for tag in self.tags.keys():
            self.textWidget.tag_remove(tag, start, end)

    # Resets/sets a timeout for re-highlighting (trying to reduce CPU usage).
    def key_press(self, key):
        if self.highlight_timeout != None:
          self.parent.after_cancel(self.highlight_timeout)
        self.highlight_timeout = self.parent.after(1500, self.rehighlight)

    # Highlights tokens according to the Highlighter class.
    def rehighlight(self):
        inMultilineComment = False
        lastLine = int(self.textWidget.index(Tkinter.END).split('.')[0])
        currentInsertLine = int(self.textWidget.index(Tkinter.INSERT).split('.')[0])
        #now loop from line = 0 to line = lastLine
        for loopLine in range(0, lastLine - 1):
            # only rehighlight up to what might have changed
            if loopLine > currentInsertLine and not inMultilineComment:
                break
            lastCol = int(self.textWidget.index('%d.end'%(loopLine)).split('.')[1])
            self.remove_tags('%d.%d'%(loopLine, 0), '%d.%d'%(loopLine, lastCol))
            start, end = 0, 0
            buffer = self.textWidget.get('%d.%d'%(loopLine,0),'%d.%d'%(loopLine,lastCol))
            # SLASH-STAR COMMENTS
            c_start = buffer.find("/*")
            c_end = buffer.find("*/")
            c_has_start = False
            c_has_end = False
            if c_start != -1:
              c_has_start = True
              inMultilineComment = True
            if c_end != -1:
              c_has_end = True
              inMultilineComment = False
            if c_has_start and c_has_end:
                self.textWidget.tag_add('comment', '%d.%d'%(loopLine, c_start), '%d.%d'%(loopLine, c_end + 2)) # + 2 to include the '*/' at the end of the comment
                buffer = buffer[c_end + 2:] # highlight from '*/' to end of line normally (+ 2 to skip the already-highlighted '*/')
            elif c_has_start and not c_has_end:
                self.textWidget.tag_add('comment', '%d.%d'%(loopLine, c_start), '%d.%d'%(loopLine, lastCol))
                continue # go to next line, this line is fully highlighted
            elif not c_has_start and c_has_end:
                self.textWidget.tag_add('comment', '%d.%d'%(loopLine, 0), '%d.%d'%(loopLine, c_end + 2)) # + 2 to include the '*/' at the end of the comment
                continue # go to next line, this line is fully highlighted
            elif inMultilineComment:
                self.textWidget.tag_add('comment', '%d.%d'%(loopLine, 0), '%d.%d'%(loopLine, lastCol))
                continue # go to next line, this line is fully highlighted
            # DOUBLE-SLASH COMMENTS
            commentColumn = buffer.find("//")
            if commentColumn != -1:
                self.textWidget.tag_add('comment', '%d.%d'%(loopLine, commentColumn), '%d.%d'%(loopLine, lastCol))
                buffer = buffer[:commentColumn] # only highlight from start of line to start of double-slash comment
            # ALL OTHER TOKEN TYPES
            nonword_regex = re.compile('\W')
            tokenized = nonword_regex.split(buffer)
            high = Highlighter.Highlighter()
            for token in tokenized:
                highlightedToken = True
                end = start + len(token)
                for tokenType, tokenTag in [(high.KEYWORDS, 'keyword'),
                (high.IDENTIFIERS, 'identifier'),
                (high.NXC_DEFS_FUNCTIONS, 'function'),
                (high.NXC_DEFS_MACROS, 'macro'),
                (high.NXC_DEFS_CONSTANTS, 'constant'),
                (high.NXC_DEFS_STRUCTS, 'struct')]:
                  if token in tokenType:
                    self.textWidget.tag_add(tokenTag, '%d.%d'%(loopLine, start), '%d.%d'%(loopLine, end))
                    highlightedToken = True
                    break
                # not any recognized token? Maybe it's a number
                # (magic numbers are bad)
                if not highlightedToken:
                    for index in range(len(token)):
                        try:
                            int(token[index])
                        except ValueError:
                            pass
                        else:
                            self.textWidget.tag_add('int', '%d.%d'%(loopLine, start+index))
                # finally, move to the next token
                start += len(token)+1
### End Syntax Highlighting


if __name__ == "__main__":
    root = Tkinter.Tk()
    # I want to tell SimpleEditor where the nbc compiler is
    # the only way I've discovered how to do this when appifying a script
    # is to get the name of the python file, strip the name off and that's
    # the directory
    # appname = sys.argv[0]
    # match = re.search("(/.*/)SimpleEditor.py", appname)
    editor = SimpleEditor(root, compiler='/usr/local/bin/nbc')
    # Open any command-line arguments not starting with '-' as files, until '--'
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == "--":
                break
            if len(arg) > 0 and arg[0] == '-':
                continue
            editor.filename = arg
            editor._open_command(arg)
    root.mainloop()
