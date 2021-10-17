from pathlib import Path


class RepoObjPath:
    def __init__(self, path: Path, type: str):
        self.path = path
        self.type = type
    
    def create_obj(self) -> None:
        try:
            if self.type == 'dir':
                self.path.mkdir(parents=True, exist_ok=True)
            
            if self.type == 'file':
                parent = self.path.parent

                parent.mkdir(parents=True, exist_ok=True)

                with self.path.open('w'): pass
        except Exception:
            raise Exception('fatal: cant create path at ' + str(self.path))