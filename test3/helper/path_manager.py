import os

import folder_paths


class PathManager:
    def __init__(self):
        # define model_paths directories
        self.model_dict = {
            "facexlib": os.path.join(folder_paths.models_dir, "facexlib"),
            "clip": os.path.join(folder_paths.models_dir, "clip"),
            "controlnet": os.path.join(folder_paths.models_dir, "controlnet"),
        }

        self._create_directories()
        self._inject_folder_paths()

    def _create_directories(self):
        for _, directory in self.model_dict.items():
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

    def _inject_folder_paths(self):
        for model_type, model_dir in self.model_dict.items():
            if not os.path.exists(model_dir):
                raise Exception(f'The model path({model_dir}) to be registered to ComfyUI does not exist!')
            if model_type in folder_paths.folder_names_and_paths:
                if isinstance(folder_paths.folder_names_and_paths[model_type][0], list):
                    folder_paths.folder_names_and_paths[model_type][0].append(model_dir)
                else:
                    raise Exception(
                        f'The registration information of this type({model_type}) of model in folder_names_and_paths '
                        f'is not a list'
                    )
            else:
                folder_paths.folder_names_and_paths[model_type] = ([model_dir], [])


path_manager = PathManager()
