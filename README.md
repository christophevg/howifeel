# How I Feel

> a small 1-hour project to show newbe developers what coding is all about

## Rationale

Starting in today's world of development of software can be daunting. Especially because the beginnings are so far apart from what we've come acustomed to when using that same software. Starting with "hello world" seems so utterly uninteresting that it takes a big effort to get past those first few days, before one reaches the level that something semi-useful can be created.

This repository is an experiment to start from a completely blanc directory and end up with an actual, useable piece of software. Each commit is a step in this experiment, described in the paragraphs below. The goal is _not_ to learn every step by heart, but to go through the entire process of conceiving and actually implementing a small real-world application. A way to get a realistic overview of what lies at the end of that first long stretch of new knowledge.

## Prerequisites

The following tools are needed and might first need some installation or creation of an account.

* A unix-like environment, say MacOS, Linux,... Why? Because that's what I use. You migth get away with Windows. I won't be here to help, sorry :-( A unix-like environment comes with a terminal, which allows you to give commands to the system. On MacOS, the Terminal application looks like this: ![Terminal](media/terminal.png)
* An editor, something to write code with. Here personal flavour kicks in. I like [TextMate](https://macromates.com), you might like something else. Please, don't hurt yourself, don't like [notepad](https://en.wikipedia.org/wiki/Windows_Notepad).
* [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
* A [GitHub account](https://github.com/join)
* [python](https://www.python.org/downloads/)
* [pyenv](https://christophe.vg/technology/Pyenv-Notes) - I refer to my own installation instruction page. You can also consult [the official pyenv documentation](https://github.com/pyenv/pyenv), which is also hosted on GitHub.
* A [Heroku account](https://signup.heroku.com)
* [MongoDB](https://docs.mongodb.com/manual/installation/)

## The Goal

We want to make a little web application that allows a user to log in and set his/her current mood - expressed as red, yellow or green.

Besides that, the user can create unique links to distribute to others, that can use that link to consult the user's mood. Those links can be deleted, removing access to certain users.

## 19:21 - git init, README.md, git push

Open up a terminal, create a directory to work in and initialize your git repository. Git repository? Git is a tool that allows you to keep track of your code as you write it.

```zsh
xtof@sokudo Workspace % mkdir howifeel
xtof@sokudo Workspace % cd howifeel
xtof@sokudo howifeel % git init
Initialized empty Git repository in /Users/xtof/Workspace/howifeel/.git/
xtof@sokudo howifeel % 
```

Because this repository contains both the application, aswell as the supporting story about writing it, I started with a first file: `README.md`, the very one you're reading right now. It's good practice to document your code, so I advise you to also always write one. It won't contain al the details of this one, but should at least include some basic information about how to install and run your application and how to contact you in case there is a problem.

In this case, you can contact _me_ through [GitHub Discussions](https://github.com/christophevg/howifeel/discussions/1) ;-)

Now time to fire up a few other git commands:

```zsh
xtof@sokudo howifeel % git add README.md
xtof@sokudo howifeel % git commit -m "repo init with README"
[master (root-commit) 93c438d] repo init with README
 1 files changed, 78 insertions(+)
 create mode 100644 README.md
```

This adds our current changes (the README file) to the "git repository" and marks it as a committed sert of changes, along with a small message that explains what this "commit" is all about.

The `.md` extension to the README file tells us that it is written in "MarkDown". This is a small, simple, text-oriented markup/layout language that is pretty convenient to write this kind of documentation. Take a look at [the code](https://github.com/christophevg/howifeel/blob/master/README.md?plain=1) that was converted into this visualisation when viewed on GitHub. 

Now, we're not done yet. We not only want to track our changes, we also want them to be safe in a place where we can share them. Enter GitHub. Head over to a browser, login to your github account and create a new "repository", let's say `howifeel`.

After creating the repository in GitHub, we add a reference to it in our own local git repository and "push" our changes to it.

```zsh
xtof@sokudo howifeel % git remote add github git@github.com:christophevg/howifeel.git
xtof@sokudo howifeel % git push -u github master
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Delta compression using up to 10 threads
Compressing objects: 100% (4/4), done.
Writing objects: 100% (5/5), 296.27 KiB | 3.25 MiB/s, done.
Total 5 (delta 0), reused 0 (delta 0), pack-reused 0
To github.com:christophevg/howifeel.git
 * [new branch]      master -> master
Branch 'master' set up to track remote branch 'master' from 'github'.
```

Now refresh the page on GitHub and behold, your first commit is online...

![Hello GitHub](media/github-first-commit.png)

Yeah!

## 19:30 - Now What do we Need to Build?

Let's reiterate our "requirements":

* a web application
* users
* update mood indicator
* create unique links
* delete unique links

### A Web Application

Everything is happening online. Of course we want our application to be online. The easiest way to get something online it through the World Wide Web (WWW), which is brought to you by your browser. 

Web applications, running in a browser are created (mainly) using HTML, the Hyper Text Markup Language... after Markdown, the second markup language we encounter and will use to create "pages" for our application.

At this point you have already been using several web applications. If not before today, you have created several accounts as part of the prerequisites.

### Users

Which brings us to "users". Just like GitHub, Heroku,... and so many other web applications, we want our users to be able to create an account to ...

###  Update Mood Indicator

... update their mood and ...

### Create Unique Links

... create unique links, which can be shared with other people.

### Delete Unique Links

And sometimes we want to those people to no longer "follow us", so we want our users to be able to remove access for those people, by deleting the unique link that was created for them.

### Pages

Let's take 5 steps back: a web application consists of pages. Each page provides a certain functionality. Let's make a list of pages we will need for our application. Think back of your experience with GitHub and Heroku, or Instagram, SnapChat,...

1. frontpage
2. sign up page
3. personal mood update page
4. manage unique links page

### An API

The web application is merely what runs in your browser. This isn't enough to be able to intertact with your followers. Their browsers won't connect directly to your browser. There is a "hidden" part in between: the server. A server does what its name says: it serves your web application to all interested parties: you, your followers,...

First of all it serves your pages to the browser. Second, it will process commands that you give using the application in your browser - let's say that I set my mood to "green", keep that mood somewhere safe and provide it to my followers when they in their turn consult the server.

This second part, the processing of commands by the server, is implemented in what is called a Application Programming Interface (API). It's an interface (something you can interact with) that allowd applications (like our web application) to use the server in a programming way. Think of it as a set of commands you can give to the server, for example:

1. show me the frontpage
2. show me the signup page
3. create an account with my information
4. show me my personal mood page
5. update my personal mood
6. show me my unique links management page
7. create a new unique link
8. delete a unique link

So, you can see there are basically two types of commands: 1) show me a page and 2) change (create/update/delete) some information.

### A Database

The server needs to store the information about me and my followers. To do this it needs another server: a database server. In this case we will be using MongoDB. There are many other possibilities. Given for this project, it is the easiest to get started with and doesn't require a lot of background knowledge. You'll thank me for choosing it.

And that's it. We have our web application, consisting of 4 pages, an API with 8 commands and a database server.

Let's start writing code...

But first, we commit this step, because small commits make a happy developer:

```zsh
xtof@sokudo howifeel % git add README.md 
xtof@sokudo howifeel % git commit -m "what do we need to build?"
[master 4a00af7] what do we need to build?
 1 file changed, 71 insertions(+)
xtof@sokudo howifeel % git push
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Delta compression using up to 10 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (3/3), 1.94 KiB | 1.94 MiB/s, done.
Total 3 (delta 1), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (1/1), completed with 1 local object.
To github.com:christophevg/howifeel.git
   2386f56..4a00af7  master -> master
```

## 19:35 - Hello Bootstrap

Stand on the shoulder of giants. It must be your credo when entering the world of code. Choosing the right tools for the job not only consist of a suitable programming language (yes, there is more than one and one doesn't fit all problems), it also means using existing components, modules, packages, frameworks,...

In this case we are going to leverage the wonderful work initiated by Twitter called [Bootstrap](https://getbootstrap.com). Bootstrap is a collection of HTML and related styling that upgrades your HTML experience to a whole new level. In stead of having to codify every little thing, you can simple think in terms of banners, buttons, etc, up to entire ready-made pages. Take a look at some [examples](https://getbootstrap.com/docs/5.1/examples/) a you'll probably notice a few pages we will happily reuse.

But first take a peek at [the bootstrap starter template](https://getbootstrap.com/docs/5.1/getting-started/introduction/#starter-template):

```html
<!doctype html>
<html lang="en">
  <head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">

    <title>Hello, world!</title>
  </head>
  <body>
    <h1>Hello, world!</h1>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p" crossorigin="anonymous"></script>
  </body>
</html>
```
Meet HTML. It consists of "tag"-pairs such as `<html>...</html>` and `<h1>...</h1>` that enclose their content and give meaning to it, e.g. `<h1>` marks up a header of the highest level, think of it as your main title.

There is in fact just a single line in those 15 lines that is really important: `<h1>Hello, world!</h1>`. All other lines are technical mumbojumbo. Save these lines to a file, say `index.html` in a new directory structure, say `src/pages`:

```zsh
xtof@sokudo howifeel % mkdir -p src/pages
```

... and open the file in a browser:

![Hello Bootstrap](media/hello-bootstrap.png)

And of course ...

```zsh
xtof@sokudo howifeel % git add README.md 
xtof@sokudo howifeel % git commit -m "introducing bootstrap and say hello"
[master ccac37b] introducing bootstrap and say hello
 2 files changed, 41 insertions(+)
xtof@sokudo howifeel % git push 
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Delta compression using up to 10 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (3/3), 1.60 KiB | 1.60 MiB/s, done.
Total 3 (delta 1), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (1/1), completed with 1 local object.
To github.com:christophevg/howifeel.git
   53d98d2..ccac37b  master -> master
```

## 19:46 - Whoops

Darn, I've made a few mistakes while writing this README: the code sections shouldn't be marked as "zsh" but "zsh", a few links are incoreectly formatted and I made a typo in the last screenshot. Let's edit those and add those changes to our repository.

Before we commit our changes, git allows us to inspect what we have changed:

```zsh
On branch master
Your branch is up to date with 'github/master'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   README.md

no changes added to commit (use "git add" and/or "git commit -a")
```

Git also allows us to see what we actually changed. You can use the command git diff` for that, though it tends to be a bit harsh on the eye at the beginning. If you install a more graphical tool, like [GitHub Desktop](https://docs.github.com/en/desktop/installing-and-configuring-github-desktop/installing-and-authenticating-to-github-desktop/installing-github-desktop) things become much nicer to look at:

![Github Desktop](media/github-desktop-diff.png)

And ...

```zsh
xtof@sokudo howifeel % git add README.md 
xtof@sokudo howifeel % git commit -m "fixing some mistakes"
[master 42bcc08] fixing some mistakes
 1 file changed, 32 insertions(+), 10 deletions(-)
xtof@sokudo howifeel % git push
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Delta compression using up to 10 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (3/3), 1.07 KiB | 1.07 MiB/s, done.
Total 3 (delta 1), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (1/1), completed with 1 local object.
To github.com:christophevg/howifeel.git
```

Our changes are now also viewable [on GitHub](https://github.com/christophevg/howifeel/commit/42bcc088b551b0bceb26dbc25de472948a8f3e78?diff=split), ready to be inspected by anyone interested in our code:

![Github diff](media/github-diff.png)

## 19:51 - Meet Python

Before we cruise on let's take 5 minutes to setup our coding environment. We'll be using the programming language called [Python](https://www.python.org/). I personally got into python roughly 10 years ago during my [renewed studying experience/experiment](https://christophe.vg/about/Revisiting_Higher_Education).

And I have never looked back ;-) Python is a wonderful, versatile, non-nonse language that allows you to quickly write something without too much fuzz, and just as well is allows you to construct beautifully structured larger code bases. One of the great things about Python is its vast and high-quality collection of modules. We'll see some of those as we move forward. Remember our "standing on the shoulders of giants" credo? The Python community really excells at this.

Another good practice you should adopt is to use "virtual environments". Virtual environments allow you to seemingly operate in a world solely dedicated to your single application. You can install Python modules, without interfering with other application on you machine. You could even use different Python versions. To manage such a virtual environment, I like to use "pyenv". Two commands create the virtual environment and activate it for this directory. It will even be re-activated everytime we enter this directory, based on the `.python-version` file, and our shell shows this by prefixing our prompt with the name of the virtual environment.

```zsh
xtof@sokudo howifeel % pyenv virtualenv howifeel
Looking in links: /var/folders/nq/xvzwtwsj25727ybthkp1wmhr0000gn/T/tmp8blbswbs
Requirement already satisfied: setuptools in /Users/xtof/.pyenv/versions/3.8.12/envs/howifeel/lib/python3.8/site-packages (56.0.0)
Requirement already satisfied: pip in /Users/xtof/.pyenv/versions/3.8.12/envs/howifeel/lib/python3.8/site-packages (21.1.1)
xtof@sokudo howifeel % pyenv local howifeel
(howifeel) xtof@sokudo howifeel % cat .python-version 
howifeel
```

Everything we do from now on, will only be executed and applied within the scope of this virtual environment. If we're ever done with it, we can even just throw it away without any garbage to clean up.

Python can be used using the `python` application, which can be given a file with python code in it, or you can just start it and feed it one command at a time. So you can do this:

```zsh
(howifeel) xtof@sokudo howifeel % python
Python 3.8.12 (default, Nov  6 2021, 10:34:02) 
[Clang 13.0.0 (clang-1300.0.29.3)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> print("Hello World")
Hello World
>>> 
```

.. or you can create a file and execute that:

```zsh
(howifeel) xtof@sokudo howifeel % echo 'print("Hello World")' > hello.py
(howifeel) xtof@sokudo howifeel % cat hello.py 
print("Hello World")
(howifeel) xtof@sokudo howifeel % python hello.py 
Hello World
```

The former really comes in handy to quickly test something before creating your actual code files.

And you know the drill..

```zsh
(howifeel) xtof@sokudo howifeel % git status
On branch master
Your branch is up to date with 'github/master'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   README.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	.python-version
	hello.py

no changes added to commit (use "git add" and/or "git commit -a")
(howifeel) xtof@sokudo howifeel % rm hello.py
(howifeel) xtof@sokudo howifeel % echo ".python-version" >> .gitignore
(howifeel) xtof@sokudo howifeel % git status
On branch master
Your branch is up to date with 'github/master'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   README.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	.gitignore

no changes added to commit (use "git add" and/or "git commit -a")
(howifeel) xtof@sokudo howifeel % git add .gitignore 
(howifeel) xtof@sokudo howifeel % git add README.md 
(howifeel) xtof@sokudo howifeel % git commit -m "introducing python and virtual environments"
[master bbfc043] introducing python and virtual environments
 2 files changed, 52 insertions(+)
 create mode 100644 .gitignore
(howifeel) xtof@sokudo howifeel % git push
Enumerating objects: 6, done.
Counting objects: 100% (6/6), done.
Delta compression using up to 10 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (4/4), 2.13 KiB | 2.13 MiB/s, done.
Total 4 (delta 1), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (1/1), completed with 1 local object.
To github.com:christophevg/howifeel.git
   98d8d72..bbfc043  master -> master
```

Before adding and committing, I inspected the changes. The `hello.py` test file can be removed, and what about the `.python-version` file? Well, it can't be removed, and it shouldn't be part of the repository, since someone else might call the environment differently, or even use another environment manager (yes there are more ;-)). So we tell git to ignore it.

