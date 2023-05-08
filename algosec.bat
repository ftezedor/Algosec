@echo off

:: check for any pyhton version
for %%P in (python2.6.exe python2.7.exe python3.3.exe python3.4.exe python3.5.exe python3.6.exe python3.7.exe python3.8.exe python3.9.exe python3.10.exe python.exe) do (
	%%P -V 1> nul 2>&1 && (
		set PTNCMD=%%P
	)
)

:: halt if not found any python interpreter
if not defined PTNCMD ( 
   echo Python is required but it could not be found 1>&2
   echo Check if it is installed and it is in PATH variable 1>&2
   exit /b
)

SET INFILE=%1
IF [%INFILE%] == [] SET INFILE=ip_list.txt

IF NOT EXIST %INFILE% (
    ECHO File '%INFILE%' not found 1>&2
    exit /b
)

SET LCKFILE=%~n0.lock

IF EXIST %LCKFILE% (
    ECHO There is an instance of %~n0 already running 1>&2
    exit /b
)

echo %date%-%time% > .\%LCKFILE%

SET CPATH=%cd%

::cd /D "%~dp0"
SET SPATH=%~dp0

shift

%PTNCMD% -W ignore "%SPATH%bin\extractor.py" %* "%INFILE%"

::echo "%SPATH%reducer.py"

cd /D %CPATH%

IF EXIST %LCKFILE% (
    DEL %LCKFILE%
)

SET CPATH=
SET LCKFILE=