# File: SimpleEditor.py
# Created: 9th May, 2013
# Creator: Brendan McCane
# License: not sure yet, some open source license

import Tkinter
import ScrolledText
#import update_mark
import tkFileDialog
import subprocess
import tkMessageBox
import re
import webbrowser
import keyword #SH
from string import ascii_letters, digits, punctuation, join #SH
import os

# a global singleton list of windows
AllWindows = []

class SimpleEditor:
    """
    A simple editor for NQC code.
    """

    # define tags for keywords, identifiers, numbers
    tags = {'kw': '#090', 'int': 'red', 'id': 'purple'}

    def __init__(self, parent):
        self.parent = parent
        # this frame contains the in-app clickable buttons
        self.menuFrame = Tkinter.Frame(parent, height=24, width=80)
        self.menuFrame.pack(side=Tkinter.TOP)

        #the pane which holds the text and the compiler
        self.pWindow = Tkinter.PanedWindow(orient=Tkinter.VERTICAL, handlesize=5, borderwidth=0, bg="#000", showhandle=True)
        self.pWindow.pack(side=Tkinter.BOTTOM, fill=Tkinter.BOTH, expand=1)

        self.textWidget = ScrolledText.ScrolledText(width=80, height=40, undo=True)
        self.textWidget.pack(fill=Tkinter.BOTH, padx=2, pady=2)

        #adds textWidget to the top of the pane
        self.pWindow.add(self.textWidget)

        # this is for the output from the compiler
        self.compilerWidget = ScrolledText.ScrolledText(width=80, height=20)
        self.compilerWidget.pack(fill=Tkinter.BOTH, padx=2, pady=2)
        self.compilerWidget.bind('<ButtonRelease>', self.find_line_num)
        self.pWindow.add(self.compilerWidget)

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
                "Compile", "Prev", "Next"]
        buttonCommands = [self.new_command, self.open_command, self.save_command, self.check_syntax, None, self.prev_error, self.next_error]
        for buttonName, buttonCommand in zip(buttonNames, buttonCommands):
            self.Button = Tkinter.Button(self.menuFrame, text=buttonName, 
                    command=buttonCommand)
            if buttonName in ["Check Syntax", "Prev"]: #space the buttons
                self.Button.pack(side=Tkinter.LEFT, padx=(20, 0))
            else:
                self.Button.pack(side=Tkinter.LEFT)
        self.lineLabel = Tkinter.Label(self.menuFrame, text="1.0", highlightthickness=1, highlightbackground="#000000")
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
        self.menuBar.add_cascade(label="File", menu=self.fileMenu)

        self.editMenu = Tkinter.Menu(parent, tearoff=0)
        self.editMenu.add_command(label="Undo", command=self.undo_command, accelerator="Ctrl+Z")
        self.editMenu.add_command(label="Redo", command=self.redo_command, accelerator="Ctrl+Y")
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

        self.commandMenu = Tkinter.Menu(self.menuBar, tearoff=0)
        self.commandMenu.add_command(label="NXC Help (opens webpage)", 
                                     command=self.open_API)
        self.menuBar.add_cascade(label="Help", menu=self.commandMenu);

        parent.config(menu=self.menuBar)

        # initialise the file associated with this window as ''
        self.filename = ''
        self.textWidget.edit_modified(False)

        # add the new object to the list of all windows.
        AllWindows.append(self)

    def new_command(self):
        """
        Create a blank new text window
        """
        root = Tkinter.Tk()
        new_editor = SimpleEditor(root)
        root.mainloop()
        return new_editor

    def open_new_command(self):
        """
        Open a new file in a new window.
        """
        root = Tkinter.Tk()
        new_editor = SimpleEditor(root)
        new_editor.open_command()
        root.mainloop()
        return new_editor

    def open_command(self):
        """
        Open an existing file in the current window
        """
        if self.filename=='':
            self.filename = tkFileDialog.askopenfilename()
            if self.filename != '':
                file = open(self.filename, "rU")
                contents = file.read()
                self.textWidget.insert(Tkinter.END, contents)
                file.close()
                self.textWidget.edit_modified(False)
                self.rehighlight()
        else:
            editor = self.open_new_command()

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
            return True
        else:
            return False

    def really_quit(self):
        del AllWindows[AllWindows.index(self)]
        print AllWindows
        self.parent.destroy()
        print "Made it here"
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

    def check_syntax(self):
        """
        Check the syntax of current contents by calling the NBC
        compiler. Needs to create a sub window for the output of the
        compiler and in the case of errors parse the output and move
        the cursor to the appropriate line.
        """
        if self.textWidget.edit_modified():
            self.save_command()
        try:
            cfile = open('.fhtyzbg.out', 'w')
            nfile = open('.flondgy.out', 'w')
            compile = subprocess.check_call(['../NBC_Mac/nbc', 
                                             self.filename, 
                                             '-O={}.rxe'.format(self.filename)],
                                            stderr=cfile, stdout=nfile) 
            cfile.close()
            nfile.close()
            self.compilerWidget.delete("1.0", Tkinter.END)
            self.compilerWidget.insert(Tkinter.END, "Hooray, compile successful")
        except subprocess.CalledProcessError as e:
            cfile.close()
            nfile.close()
            cfile = open('.fhtyzbg.out', 'rU')
            lines = cfile.readlines()
            cfile.close()
            lines = [x for x in lines if not x.startswith('# Status')]
            self.error_lines = []
            self.error_pos = -1
            for line in lines:
                m = re.search('(line) ([0-9]+)', line)
                if m is not None:
                    if m.lastindex==2:
                        self.error_lines += [int(m.group(2))]
            output = ''.join(lines)
            self.compilerWidget.delete("1.0", Tkinter.END)
            self.compilerWidget.insert(Tkinter.END, output)

        os.remove('.fhtyzbg.out')
        os.remove('.flondgy.out')

    def compile_upload(self):
        """
        Compile and upload the program to an actual lego brick. Again
        using the NBC compiler.
        """
        pass

    def highlight_current_line(self):
        self.textWidget.tag_remove("current_line", 1.0, "end")
        self.textWidget.tag_add("current_line", "insert linestart", "insert lineend")

    def goto_line(self, linenum):
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

    def open_API(self):
        """
        Eventually pop up some form of useful information on functions that
        NXC uses
        """
        webbrowser.open("http://bricxcc.sourceforge.net/nbc/nxcdoc/nxcapi/index.html")
        api_test = subprocess.check_output(['../NBC_Mac/nbc -api', 
                                        self.filename, 
                                        '-O={}.rxe'.format(self.filename)],
                                       stderr=subprocess.STDOUT) 
        print api_test

    def update_linenum_label(self, event):
      self.lineLabel.config(text=self.textWidget.index('insert'))

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

    def key_press(self, key):
        self.rehighlight()

    def rehighlight(self):
        # loop through every line... VERY INEFFICIENT
        lastline = int(self.textWidget.index(Tkinter.END).split('.')[0])
        #cline = self.textWidget.index(Tkinter.INSERT).split('.')[0]
        #now loop from line = 0 to line = lastline
        for cline in range(0, lastline - 1):
            lastcol = 0
            char = self.textWidget.get('%d.%d'%(cline, lastcol))
            # Stuck in infinite loop here :(
            while char != '\n':
                lastcol += 1
                char = self.textWidget.get('%d.%d'%(cline, lastcol))
                if lastcol > 80: # temp hack to break infinite loop
                    break

            buffer = self.textWidget.get('%d.%d'%(cline,0),'%d.%d'%(cline,lastcol))
            tokenized = buffer.split(' ')

            self.remove_tags('%d.%d'%(cline, 0), '%d.%d'%(cline, lastcol))

            start, end = 0, 0
            for token in tokenized:
                end = start + len(token)
                identifiers = ["bool", "byte", "char", "const", "enum", "float", "int", "long",
                           "mutex", "short", "static", "string", "typedef", "unsigned",
                           "struct"]
                keywords = ["asm", "break", "case", "continue", "do", "if", "else",
                "for", "goto", "priority", "repeat", "return", "start", "stop",
                "switch", "until", "while", "default", "inline", "safecall",
                "sub", "void", "true", "false"]
                if token in keywords:
                    self.textWidget.tag_add('kw', '%d.%d'%(cline, start), '%d.%d'%(cline, end))
                elif token in identifiers:
                    self.textWidget.tag_add('id', '%d.%d'%(cline, start), '%d.%d'%(cline, end))
                else:
                    for index in range(len(token)):
                        try:
                            int(token[index])
                        except ValueError:
                            pass
                        else:
                            self.textWidget.tag_add('int', '%d.%d'%(cline, start+index))
                start += len(token)+1
### End Syntax Highlighting


if __name__ == "__main__":
    root = Tkinter.Tk()
    editor = SimpleEditor(root)
    root.mainloop()
