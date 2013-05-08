RobotsRepo
==========

The initial repo for the Robots team.

The robots team is going to work on a cross-platform IDE/compiler for lego robots. I think what we want to create is something a bit like RobotC (which works well on Windows but not on anything else). However, neither the language nor the environment need be the same, but that is the sort of thing we're chasing. Relatively easy to use and hopefully reliable.

==========
To do:

Initially there are two related tasks. The first is to investigate what open-source tools are already available and see if they can be co-opted into the project and developed further. For example, we might try and make use of the nxc compiler.

The second task is to do some requirements gathering. There are a few potential sources of information here. Sandy Garner has a need for a friendly development environment to support the kids in her schoolchildren robotics clubs. Also the 3rd year AI students and staff make use of a particular environment for programming the robots in one of the assignments (I believe they aren't particularly enthused about the environment they have).

Once we have those two bits of information, we can decide what the next steps should be.

=====================


5th May 2013
This project seems to have stalled.
We need to make a decision about what this group is actually doing.
The environment used in COSC343 has publically avaliable source code, which has been released under the Mozilla Public
License. My suggestion is we try and improve it, adding the things people in 343 found lacking (syntax highlighting,
multiple windows open etc). One issue with this is that it is written in Delphi, which I imagine none of us know.
So a first step could be to start poking around, reading the code in order to get some understanding of it.
The souce code can be found here - http://sourceforge.net/p/bricxcc/code/HEAD/tree/

=====================

6th May 2013
Yes we have certainly stalled. Unfortunately I just haven't had the time to get things started by giving everyone a poke. Thanks for the push Gene. You're idea above is a good one, but I'd like to suggest a small change. The Bricxcc IDE is quite a large system, but it basically makes use of NXC and NBC as the compiler for the lego robots. I think we can simply use that compiler to do a lot of the heavy lifting and build an IDE on top of it (basically what Bricxcc does). We can do that by incorporating the NXC/NBC compilers into any distribution. This has the benefit of not being tied to delphi. We can then choose either a cross-platform environment for building the IDE (e.g. C++ with QT, or Python with one of it's toolkits), or specifically choose Mac (Objective-C with the OSX framework). My preference would be for a cross-platform environment (with a slight preference for python because I know how to get something started quickly).

======================

7th May 2013
I have added the nbc/nxc compiler (macos executable) to the project in the directory NBC_Mac. We should be able to use this initially at least with a fairly straightforward editor.

====================

2013-05-08
An IDE written in Python based on top of the existing compilers meets our goals and uses skils we already have or we can
quickly develop (Python syntax easy, C-like syntax not so much). Would we write a Python editor from scratch, or could we
utilise something from http://http://wiki.python.org/moin/PythonEditors ? As a random choice from this list, wxKonTEXT
doesn't look horrible - http://soft.kaworu.it/img/winzozz.png - source and binaries available here:
http://soft.kaworu.it/wxKonTEXTen.htm.
