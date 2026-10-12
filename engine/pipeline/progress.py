"""Numeric render progress is distinct from technical verification and readiness."""
from datetime import datetime,timezone

class RenderProgress:
    def __init__(self,total_us,callback):self.total_us=total_us;self.processed_us=0;self.callback=callback
    def line(self,line):
        key,_,value=line.strip().partition('=')
        if key=='out_time_us':
            try:measured=int(value)
            except ValueError:return
            self.processed_us=max(self.processed_us,min(self.total_us,max(0,measured)))
            self.callback(self.processed_us,self.total_us)

def activity_time():return datetime.now(timezone.utc).isoformat()
