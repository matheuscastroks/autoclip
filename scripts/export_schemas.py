import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from engine.contracts import models
target=root/'engine/contracts/schemas';target.mkdir(exist_ok=True)
for name in ['Source','AudioArtifact','TranscriptArtifact','AnalysisArtifact','CandidateArtifact','EDLArtifact','CropArtifact','CaptionArtifact','ReviewDecision','StageRequest','StageResult','ProjectRun']:
    (target/(name+'.json')).write_text(json.dumps(getattr(models,name).model_json_schema(),ensure_ascii=False,indent=2),encoding='utf-8')
print('Exported 12 versioned schemas.')
