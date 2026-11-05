dl-conv-dram2 (2026-11-05 00:38-00:45): INVALID. queue_i2.sh's trigger (grep "all done 3" on queue.txt) matched a note I had appended to
queue.txt at 00:37 that quoted the trigger string, so the lighter-load sweep started while d-tool-dram2 was running. Its own vLLM server
could not start (port 8100 / GPU in use), its readiness poll saw the OTHER run's servers, and it sent its 599 conversation requests to
d-tool-dram2's server from 00:38:47 until it was killed at 00:45. These records were served by the wrong server configuration (tool-agent
run's 2 GB L1, shared with the tool-agent load). d-tool-dram2 (0.08x) is contaminated by the same requests and is re-run at the end of the
queue (dl2 queue); its original files are moved here as d-tool-dram2-contaminated-* once the run ends.
