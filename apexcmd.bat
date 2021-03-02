@ECHO OFF
C:
set PYTHONHOME=
set PYTHONPATH=
REM Set the current directory to the location of apex
cd C:\apex\
call python apexcmd.py --profile %1
