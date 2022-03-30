##!/usr/bin/env python3


#### PYTHON IMPORTS ################################################################################
import datetime
import os
import sys
from pathlib import Path


#### PACKAGE IMPORTS ###############################################################################


#### GLOBALS #######################################################################################
ISSUES_HEADER = ["REPO_URL", "REPO_NAME", "REPO_OWNER", "ISSUE_NUMBER", "ISSUE_CREATION_DATE",
    "ISSUE_AUTHOR", "ISSUE_TITLE", "ISSUE_URL", "ISSUE_TEXT", "COMMENT_CREATION_DATE",
    "COMMENT_AUTHOR", "COMMENT_URL", "COMMENT_TEXT"]
COMMITS_HEADER = ["REPO_URL", "REPO_NAME", "REPO_OWNER", "COMMIT_OID", "COMMIT_CREATION_DATE",
    "COMMIT_AUTHOR", "COMMIT_ADDITIONS", "COMMIT_DELETIONS", "COMMIT_HEADLINE", "COMMIT_URL",
    "COMMIT_TEXT", "COMMENT_CREATION_DATE", "COMMENT_AUTHOR", "COMMENT_URL", "COMMENT_TEXT"]
PULL_REQUESTS_HEADER = ["REPO_URL", "REPO_NAME", "REPO_OWNER", "PULL_REQUEST_NUMBER",
    "PULL_REQUEST_TITLE", "PULL_REQUEST_AUTHOR", "PULL_REQUEST_CREATION_DATE", "PULL_REQUEST_URL",
    "PULL_REQUEST_TEXT", "COMMENT_CREATION_DATE", "COMMENT_AUTHOR", "COMMENT_URL", "COMMENT_TEXT"]
BAD_CHARS = [
    "…", "\xe2\x80\xa6"
]
# All filterable languages grabbed from GitHub's page source on 2021-08-31.
GITHUB_LANGUAGES = [
    "1C Enterprise", "4D", "ABAP", "ABAP CDS", "ABNF", "ActionScript", "Ada", "Adobe Font Metrics",
    "Agda", "AGS Script", "AIDL", "AL", "Alloy", "Alpine Abuild", "Altium Designer", "AMPL",
    "AngelScript", "Ant Build System", "ANTLR", "ApacheConf", "Apex", "API Blueprint", "APL",
    "Apollo Guidance Computer", "AppleScript", "Arc", "AsciiDoc", "ASL", "ASN.1", "AspectJ",
    "ASP.NET", "Assembly", "Astro", "Asymptote", "ATS", "Augeas", "AutoHotkey", "AutoIt", "Avro IDL",
    "Awk", "Ballerina", "BASIC", "Batchfile", "Beef", "Befunge", "BibTeX", "Bicep", "Bison",
    "BitBake", "Blade", "BlitzBasic", "BlitzMax", "Bluespec", "Boo", "Boogie", "Brainfuck",
    "Brightscript", "Browserslist", "C", "C#", "C++", "C2hs Haskell", "Cabal Config", "Cap'n Proto",
    "CartoCSS", "Ceylon", "Chapel", "Charity", "ChucK", "CIL", "Cirru", "Clarion", "Classic ASP",
    "Clean", "Click", "CLIPS", "Clojure", "Closure Templates", "Cloud Firestore Security Rules",
    "CMake", "C-ObjDump", "COBOL", "CODEOWNERS", "CodeQL", "CoffeeScript", "ColdFusion",
    "ColdFusion CFC", "COLLADA", "Common Lisp", "Common Workflow Language", "Component Pascal",
    "CoNLL-U", "Cool", "Coq", "Cpp-ObjDump", "Creole", "Crystal", "CSON", "Csound", "Csound Document",
    "Csound Score", "CSS", "CSV", "Cuda", "CUE", "Cue Sheet", "cURL Config", "CWeb", "Cycript",
    "Cython", "D", "Dafny", "Darcs Patch", "Dart", "DataWeave", "desktop", "Dhall", "Diff",
    "DIGITAL Command Language", "dircolors", "DirectX 3D File", "DM", "DNS Zone", "D-ObjDump",
    "Dockerfile", "Dogescript", "DTrace", "Dylan", "E", "Eagle", "Easybuild", "EBNF", "eC",
    "Ecere Projects", "ECL", "ECLiPSe", "EditorConfig", "Edje Data Collection", "edn", "Eiffel",
    "EJS", "Elixir", "Elm", "Emacs Lisp", "E-mail", "EmberScript", "EQ", "Erlang", "F#", "F*",
    "Factor", "Fancy", "Fantom", "Faust", "Fennel", "FIGlet Font", "Filebench WML", "Filterscript",
    "fish", "Fluent", "FLUX", "Formatted", "Forth", "Fortran", "Fortran Free Form", "FreeBasic",
    "FreeMarker", "Frege", "Futhark", "Game Maker Language", "GAML", "GAMS", "GAP",
    "GCC Machine Description", "G-code", "GDB", "GDScript", "GEDCOM", "Gemfile.lock", "Genie",
    "Genshi", "Gentoo Ebuild", "Gentoo Eclass", "Gerber Image", "Gettext Catalog", "Gherkin",
    "Git Attributes", "Git Config", "GLSL", "Glyph", "Glyph Bitmap Distribution Format", "GN",
    "Gnuplot", "Go", "Golo", "Gosu", "Grace", "Gradle", "Grammatical Framework",
    "Graph Modeling Language", "GraphQL", "Graphviz (DOT)", "Groovy", "Groovy Server Pages", "Hack",
    "Haml", "Handlebars", "HAProxy", "Harbour", "Haskell", "Haxe", "HCL", "HiveQL", "HLSL", "HolyC",
    "HTML", "HTML+ECR", "HTML+EEX", "HTML+ERB", "HTML+PHP", "HTML+Razor", "HTTP", "HXML", "Hy",
    "HyPhy", "IDL", "Idris", "Ignore List", "IGOR Pro", "ImageJ Macro", "Inform 7", "INI",
    "Inno Setup", "Io", "Ioke", "IRC log", "Isabelle", "Isabelle ROOT", "J", "Jasmin", "Java",
    "Java Properties", "JavaScript", "JavaScript+ERB", "Java Server Pages", "JFlex", "Jinja",
    "Jison", "Jison Lex", "Jolie", "jq", "JSON", "JSON5", "JSONiq", "JSONLD", "Jsonnet",
    "JSON with Comments", "Julia", "Jupyter Notebook", "Kaitai Struct", "KakouneScript",
    "KiCad Layout", "KiCad Legacy Layout", "KiCad Schematic", "Kit", "Kotlin", "KRL", "Kusto",
    "LabVIEW", "Lark", "Lasso", "Latte", "Lean", "Less", "Lex", "LFE", "LilyPond", "Limbo",
    "Linker Script", "Linux Kernel Module", "Liquid", "Literate Agda", "Literate CoffeeScript",
    "Literate Haskell", "LiveScript", "LLVM", "Logos", "Logtalk", "LOLCODE", "LookML", "LoomScript",
    "LSL", "LTspice Symbol", "Lua", "M", "M4", "M4Sugar", "Macaulay2", "Makefile", "Mako",
    "Markdown", "Marko", "Mask", "Mathematica", "MATLAB", "Maven POM", "Max", "MAXScript",
    "mcfunction", "Mercury", "Meson", "Metal", "Microsoft Developer Studio Project",
    "Microsoft Visual Studio Solution", "MiniD", "Mirah", "mIRC Script", "MLIR", "Modelica",
    "Modula-2", "Modula-3", "Module Management System", "Monkey", "Moocode", "MoonScript",
    "Motorola 68K Assembly", "MQL4", "MQL5", "MTML", "MUF", "mupad", "Muse", "Mustache", "Myghty",
    "nanorc", "NASL", "NCL", "Nearley", "Nemerle", "NEON", "nesC", "NetLinx", "NetLinx+ERB",
    "NetLogo", "NewLisp", "Nextflow", "Nginx", "Nim", "Ninja", "Nit", "Nix", "NL", "NPM Config",
    "NSIS", "Nu", "NumPy", "Nunjucks", "NWScript", "ObjDump", "Object Data Instance Notation",
    "Objective-C", "Objective-C++", "Objective-J", "ObjectScript", "OCaml", "Odin", "Omgrofl", "ooc",
    "Opa", "Opal", "OpenCL", "OpenEdge ABL", "Open Policy Agent", "OpenQASM", "OpenRC runscript",
    "OpenSCAD", "OpenStep Property List", "OpenType Feature File", "Org", "Ox", "Oxygene", "Oz", "P4",
    "Pan", "Papyrus", "Parrot", "Parrot Assembly", "Parrot Internal Representation", "Pascal", "Pawn",
    "PEG.js", "Pep8", "Perl", "PHP", "Pic", "Pickle", "PicoLisp", "PigLatin", "Pike", "PlantUML",
    "PLpgSQL", "PLSQL", "Pod", "Pod 6", "PogoScript", "Pony", "PostCSS", "PostScript", "POV-Ray SDL",
    "PowerBuilder", "PowerShell", "Prisma", "Processing", "Proguard", "Prolog", "Propeller Spin",
    "Protocol Buffer", "Public Key", "Pug", "Puppet", "PureBasic", "Pure Data", "PureScript",
    "Python", "Python console", "Python traceback", "q", "Q#", "QMake", "QML", "Qt Script", "Quake",
    "R", "Racket", "Ragel", "Raku", "RAML", "Rascal", "Raw token data", "RDoc", "Readline Config",
    "REALbasic", "Reason", "Rebol", "Record Jar", "Red", "Redcode", "Redirect Rules",
    "Regular Expression", "RenderScript", "Ren'Py", "ReScript", "reStructuredText", "REXX",
    "Rich Text Format", "Ring", "Riot", "RMarkdown", "RobotFramework", "robots.txt", "Roff",
    "Roff Manpage", "Rouge", "RPC", "RPM Spec", "Ruby", "RUNOFF", "Rust", "Sage", "SaltStack", "SAS",
    "Sass", "Scala", "Scaml", "Scheme", "Scilab", "SCSS", "sed", "Self", "SELinux Policy",
    "ShaderLab", "Shell", "ShellSession", "Shen", "Sieve", "Singularity", "Slash", "Slice", "Slim",
    "Smali", "Smalltalk", "Smarty", "SmPL", "SMT", "Solidity", "Soong", "SourcePawn", "SPARQL",
    "Spline Font Database", "SQF", "SQL", "SQLPL", "Squirrel", "SRecode Template", "SSH Config",
    "Stan", "Standard ML", "Starlark", "Stata", "STON", "StringTemplate", "Stylus", "SubRip Text",
    "SugarSS", "SuperCollider", "Svelte", "SVG", "Swift", "SWIG", "SystemVerilog", "Tcl", "Tcsh",
    "Tea", "Terra", "TeX", "Texinfo", "Text", "Textile", "TextMate Properties", "Thrift",
    "TI Program", "TLA", "TOML", "TSQL", "TSV", "TSX", "Turing", "Turtle", "Twig", "TXL",
    "Type Language", "TypeScript", "Unified Parallel C", "Unity3D Asset", "Unix Assembly", "Uno",
    "UnrealScript", "UrWeb", "V", "Vala", "Valve Data Format", "VBA", "VBScript", "VCL", "Verilog",
    "VHDL", "Vim Help File", "Vim script", "Vim Snippet", "Visual Basic .NET", "Volt", "Vue",
    "Wavefront Material", "Wavefront Object", "wdl", "WebAssembly", "WebIDL", "Web Ontology Language",
    "WebVTT", "Wget Config", "Wikitext", "Windows Registry Entries", "wisp", "Wollok",
    "World of Warcraft Addon Data", "X10", "xBase", "X BitMap", "XC", "XCompose",
    "X Font Directory Index", "XML", "XML Property List", "Xojo", "Xonsh", "XPages", "X PixMap",
    "XProc", "XQuery", "XS", "XSLT", "Xtend", "Yacc", "YAML", "YANG", "YARA", "YASnippet", "ZAP",
    "Zeek", "ZenScript", "Zephir", "Zig", "ZIL", "Zimpl", "None"
]
# You will likely notice that this list only contains 47 languages. The TIOBE Index lists "Ladder
# Logic" and "(Visual) FoxPro", which are not languages you can filter for on GitHub. It also lists
# "Visual Basic" and "Classic Visual Basic" separately, but the closest match for GitHub filtering
# is "Visual Basic .NET", which is in the list below. Additionally, "Delphi/Object Pascal" is listed
# below as "Pascal", "Logo" as "Logos", and "Bash" as "Shell".
TIOBE_INDEX_TOP_50_AUG_2021 = [
    "ABAP", "Ada", "Apex", "Assembly", "C", "C#", "C++", "Clojure", "COBOL", "D", "Dart", "F#",
    "Fortran", "Go", "Groovy", "Java", "JavaScript", "Julia", "Kotlin", "LabVIEW", "Lisp", "Logos",
    "Lua", "MATLAB", "Nim", "Objective-C", "Pascal", "Perl", "PHP", "Prolog", "Python", "R", "Ruby",
    "Rust", "SAS", "Scala", "Scheme", "Scratch", "Shell", "SQL", "SQLPL", "Swift", "TSQL",
    "TypeScript", "VBScript", "VHDL", "Visual Basic .NET"
]
# All popular languages grabbed from GitHub's page source on 2021-08-31.
GITHUB_POPULAR_AUG_2021 = [
    "C", "C#", "C++", "CoffeeScript", "CSS", "Dart", "DM", "Elixir", "Go", "Groovy", "HTML", "Java",
    "JavaScript", "Kotlin", "Objective-C", "Perl", "PHP", "PowerShell", "Python", "Ruby", "Rust",
    "Scala", "Shell", "Swift", "TypeScript"
]
COMBINED_LANGUAGES = sorted(list(set(TIOBE_INDEX_TOP_50_AUG_2021).union(GITHUB_POPULAR_AUG_2021)))
TEST_LANGUAGES = [
    "C", "C++", "C#", "Java", "JavaScript", "PHP", "Python", "Ruby", "Shell", "TypeScript"
]


#### CLASSES #######################################################################################
class InvalidGitHubURLError(Exception):
    """
    Exception raised by parseRepoURL() when the provided input is not a valid GitHub repository.
    """
    pass


#### FUNCTIONS #####################################################################################
def fixNullBytes(file_pointer):
    """
    Replaces null bytes with "<NULL>" so csv.reader() doesn't produce an error.

    GIVEN:
      file_pointer (...) -- pointer to an open file
    """
    for line in file_pointer:
        yield line.replace("\0", "<NULL>")


def canonicalize(path):
    """
    Helper function to canonicalize filepaths.

    GIVEN:
      path (str) -- a filepath to canonicalize

    RETURN:
      ____ (str) -- a canonicalized filepath
    """
    return os.path.realpath(path)


def doesPathExist(path):
    """
    Helper function to determine if a filepath exists.

    GIVEN:
      path (str) -- a filepath to check for existence

    RETURN:
      ____ (bool) -- True if the given filepath exists, False otherwise
    """
    return os.path.exists(path)


def validateDataDir(data_dir):
    """
    Check the data_dir for the existence of required subdirectories. If they do not exist, create
    them.

    GIVEN:
      data_dir (str) -- directory path to check
    """
    issues_path = os.path.join(data_dir, "issues/")
    commits_path = os.path.join(data_dir, "commits/")
    pull_requests_path = os.path.join(data_dir, "pull_requests/")

    if not doesPathExist(issues_path):
        os.mkdir(issues_path)
        Path(os.path.join(issues_path), "__init__.py").touch()
        #print("Created: {}".format(issues_path))
    else:
        Path(os.path.join(issues_path), "__init__.py").touch()
    
    if not doesPathExist(commits_path):
        os.mkdir(commits_path)
        Path(os.path.join(commits_path), "__init__.py").touch()
        #print("Created: {}".format(commits_path))
    else:
        Path(os.path.join(commits_path), "__init__.py").touch()
    
    if not doesPathExist(pull_requests_path):
        os.mkdir(pull_requests_path)
        Path(os.path.join(pull_requests_path), "__init__.py").touch()
        #print("Created: {}".format(pull_requests_path))
    else:
        Path(os.path.join(pull_requests_path), "__init__.py").touch()


def parseRepoURL(repo_url):
    """
    Parse a repository URL and grab the owner and name fields.

    GIVEN:
      repo_url (str) -- URL to parse; e.g. https://github.com/meyersbs/SPLAT

    RETURN:
      repo_owner (str) -- the owner of the repo; e.g. meyersbs
      repo_name (str) -- the name of the repo; e.g. SPLAT
    """

    if not repo_url.startswith("https://github.com/"):
        raise InvalidGitHubURLError(
            "The URL '{}' is not a valid GitHub repository.".format(repo_url))

    repo_owner = repo_url.split("/")[3]
    repo_name = repo_url.split("/")[4]

    return repo_owner, repo_name


def getSubDirNames(top_dir):
    """
    Get the names of subdirectories, one level deep.
    """
    return [d[1] for d in os.walk(top_dir)][0]


def getDataFilepaths(data_dir):
    """
    Get filepaths for issues, commits, and pull requests in the given data_dir.

    GIVEN:
      data_dir (str) -- absolute path to data

    RETURN:
      issues_file (str) -- absolute path to issues CSV
      commits_file (str) -- absolute path to commits CSV
      pull_requests_file (str) -- absolute path to pull requests CSV
    """

    issues_file = os.path.join(data_dir, "issues/issues.csv")
    commits_file = os.path.join(data_dir, "commits/commits.csv")
    pull_requests_file = os.path.join(data_dir, "pull_requests/pull_requests.csv")

    return [issues_file, commits_file, pull_requests_file]


def overwriteFile(old_file, new_file): # pragma: no cover
    """
    Overwrite old_file with new_file.

    GIVEN:
      old_file (str) -- path to file to overwrite
      new_file (str) -- path to file to overwrite old_file with

    RETURN:
      None
    """
    # Delete old_file
    if doesPathExist(old_file):
        os.remove(old_file)

    # Rename new_file to old_file
    os.rename(new_file, old_file)


#### MAIN ##########################################################################################
if __name__ == "__main__": # pragma: no cover
    sys.exit("This file is not intended to be run independently. Please execute './main.py' to "
             "access this functionality.")
