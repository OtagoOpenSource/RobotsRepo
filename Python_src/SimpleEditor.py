# File: SimpleEditor.py
# Created: 9th May, 2013
# Creator: Brendan McCane
# License: not sure yet, some open source license

import Tkinter
import ScrolledText
import tkFileDialog
import subprocess
import tkMessageBox

# a global singleton list of windows
AllWindows = []

class SimpleEditor:
    """
    A simple editor for NQC code.
    """

    def __init__(self, parent):
        self.parent = parent
        # this frame contains the in-app clickable buttons
        self.menuFrame = Tkinter.Frame(parent, height=24, width=80);
        self.menuFrame.grid(row=0,column=0)

        self.textWidget = ScrolledText.ScrolledText(parent, width=80, height=50)
        self.textWidget.grid(row=1,column=0)

        # this is for the output from the compiler
        self.compilerWidget = ScrolledText.ScrolledText(parent, width=80, height=20)
        self.compilerWidget.grid(row=2,column=0)

        # set up the menus
        #set up clickable buttons
        buttonNames = ["New", "Open", "Save", "Check Syntax",
				"Compile", "Prev", "Next"]
        buttonCommands = [self.new_command, self.open_command, self.save_command,
                self.check_syntax, None, None, None]
        for buttonName, buttonCommand in zip(buttonNames, buttonCommands):
            self.Button = Tkinter.Button(self.menuFrame, text=buttonName, 
                command=buttonCommand)
            if buttonName in ["Check Syntax", "Prev"]: #space the buttons
                self.Button.pack(side=Tkinter.LEFT, padx=(20, 0))
            else:
                self.Button.pack(side=Tkinter.LEFT)
        # todo - add shortcuts and possible shortcut icons
        self.menuBar = Tkinter.Menu(parent, tearoff=0)
        self.fileMenu = Tkinter.Menu(self.menuBar, tearoff=0)
        self.fileMenu.add_command(label="New", underline=1, command=self.new_command, accelerator="Ctrl+N")
        self.fileMenu.add_command(label="Open", command=self.open_command)
        self.fileMenu.add_command(label="Save", command=self.save_command)
        self.fileMenu.add_command(label="Save As", command=self.saveas_command)
        self.fileMenu.add_command(label="Close", command=self.close_command)
        self.fileMenu.add_command(label="Quit", command=self.quit_command)
        self.menuBar.add_cascade(label="File", menu=self.fileMenu)
        
        self.commandMenu = Tkinter.Menu(self.menuBar, tearoff=0)
        self.commandMenu.add_command(label="Check Syntax", 
                                     command=self.check_syntax)
        self.commandMenu.add_command(label="Compile and Upload", 
                                     command = self.compile_upload)
        self.menuBar.add_cascade(label="Compile", menu=self.commandMenu)

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

    def open_command(self):
        """
        Open an existing file in the current window
        """
        if self.filename=='':
            self.filename = tkFileDialog.askopenfilename()
            if self.filename != '':
                file = open(self.filename, "r")
                contents = file.read()
                self.textWidget.insert(Tkinter.END, contents)
                file.close()
                self.textWidget.edit_modified(False)
        else:
            editor = self.new_command()

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
            compile = subprocess.check_output(['../NBC_Mac/nbc', 
                                               self.filename, 
                                               '-O={}.rxe'.format(self.filename)],
                                              stderr=subprocess.STDOUT) 
            self.compilerWidget.delete("1.0", Tkinter.END)
            self.compilerWidget.insert(Tkinter.END, "Hooray, compile successful")
        except subprocess.CalledProcessError as e:
            lines = e.output.splitlines()
            lines = [x for x in lines if not x.startswith('# Status')]
            output = '\n'.join(lines)
            self.compilerWidget.delete("1.0", Tkinter.END)
            self.compilerWidget.insert(Tkinter.END, output)

    def compile_upload(self):
        """
        Compile and upload the program to an actual lego brick. Again
        using the NBC compiler.
        """
        pass


if __name__ == "__main__":
    root = Tkinter.Tk()
    editor = SimpleEditor(root)
    root.mainloop()
