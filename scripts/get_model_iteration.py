import logging
import os
import json
import rcs
from maple_structures import ModelIteration, Model, Processed, Topic, Article
from maple_interface import MapleAPI

    
    
class RTPT:
    def __init__(self, maple_api: MapleAPI, path: str) -> None:
        self.maple = maple_api
        if not os.path.exists(path):
            raise FileNotFoundError("invalid path provided %s", path)
        self._path = path

    @classmethod
    def load(cls, path: str):
        pass
    
    @classmethod
    def get_by_model_iteration(cls, maple_api: MapleAPI, model_iteration_uuid: str, **kwargs):
        rtpt = cls(maple_api=maple_api, **kwargs)
        
        # TODO download data
        return rtpt
    
    def _fake_download(self, model_iteration_uuid: str):
        pass
        

def download_data(maple: MapleAPI, model_iteration_uuid: str, path: str):
    if not os.path.exists(path):
        raise FileNotFoundError('Invalid path')
    
    # TODO modify to find by uuid
    model_iteration_objs = maple.model_iteration_get()
    
    if not isinstance(model_iteration_objs, list):
        raise ValueError('Failed to retrieve data.')
    
    model_iteration = None
    for model_iteration_obj in model_iteration_objs:
        if model_iteration_obj.uuid == model_iteration_uuid:
            model_iteration = model_iteration_obj
            break
    
    if not model_iteration:
        raise ValueError('Failed to download data.')

    # create directory
    model_iteration_path = os.path.join(path, model_iteration.uuid)
    try:
        os.makedirs(model_iteration_path, exist_ok=True)
    except OSError:
        raise
    
    with open(os.path.join(model_iteration_path, 'model_iteration.json'), 'w') as file:
        json.dump(model_iteration.to_dict(), file, indent=2)
    
    processed = []
    skip = 0
    while True:    
        limit = 1000
        response = maple.processed_get(model_iteration_uuid, limit=limit, skip=skip, as_json=True)
        if not isinstance(response,list):
            continue
        if len(response) == 0:
            break 
        processed.extend(response)
        skip += limit
        
    with open(os.path.join(model_iteration_path, 'processed.json'), 'w') as file:
        json.dump(processed, file, indent=2)
    
    def article_in_processed(article, processed_list):
        for processed in processed_list:
            if article.uuid == processed['article']['uuid']:
                return True
        return False
    
    articles_out = []
    for articles in maple.article_iterator():
        for article in articles:  
            if article_in_processed(article, processed):
                articles_out.append(article.to_dict())
    
    with open(os.path.join(model_iteration_path, 'article.json'), 'w') as file:
        json.dump(articles_out, file, indent=2)

if __name__ == '__main__':
    DATAPATH = 'data'
    MODEL_ITERATION_UUID = '75782439-fa4c-479b-9428-6749a56364f1'
    rcs.utils.configure_logging()
    maple_api = MapleAPI(authority = 'http://localhost:3000')
    download_data(maple=maple_api, model_iteration_uuid=MODEL_ITERATION_UUID, path=DATAPATH)
    # rtpt = RTPT.get_by_model_iteration(
    #     maple_api=maple_api, 
    #     uuid='75782439-fa4c-479b-9428-6749a56364f1',
    #     path = DATAPATH)




