@echo off
echo WARNING: This will delete 'backend' and 'frontend' and move 'verification_engine' to the root.
echo Press Ctrl+C to cancel, or any key to continue.
pause

echo Deleting 'backend' folder...
if exist backend rmdir /s /q backend

echo Deleting 'frontend' folder...
if exist frontend rmdir /s /q frontend

echo Moving 'verification_engine' contents to root...
xcopy /E /H /Y verification_engine\* .

echo Cleaning up 'verification_engine' folder...
if exist verification_engine rmdir /s /q verification_engine

echo Migration Complete. Your root directory is now the Verification Engine.
pause
