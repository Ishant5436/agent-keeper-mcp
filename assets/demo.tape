# VHS Tape for AgentKeeper-MCP Demo
Output "assets/agent_keeper_demo.gif"
Output "assets/agent_keeper_demo.mp4"

Set FontSize 14
Set Width 1200
Set Height 700
Set Padding 20
Set Theme "TokyoNight"
Set TypingSpeed 25ms

Type "python3 -m pytest -v"
Enter
Sleep 5s

Type "python3 -m unittest discover -s tests"
Enter
Sleep 4s

Sleep 2s
