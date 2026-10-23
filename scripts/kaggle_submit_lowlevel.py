"""Low-level Kaggle submit: start upload / finish submission (token auth).

The kaggle 2.2.5 client's single streaming PUT can stall on some networks;
this splits it into explicit steps so the transfer can be done with curl.

Usage:
  KAGGLE_API_TOKEN=... python scripts/kaggle_submit_lowlevel.py start FILE OUT.json
  curl -T FILE "$(python -c "import json;print(json.load(open('OUT.json'))['url'])")"
  KAGGLE_API_TOKEN=... python scripts/kaggle_submit_lowlevel.py finish OUT.json "message"
"""

from __future__ import annotations

import json
import os
import sys

COMP = 'google-verifiable-quantum-circuit-compilation'


def client():
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    return api


def main() -> None:
    cmd = sys.argv[1]
    if cmd == 'start':
        path, out = sys.argv[2], sys.argv[3]
        from kaggle.api.kaggle_api_extended import ApiStartSubmissionUploadRequest
        api = client()
        req = ApiStartSubmissionUploadRequest()
        req.competition_name = COMP
        req.file_name = os.path.basename(path)
        req.content_length = os.path.getsize(path)
        req.last_modified_epoch_seconds = int(os.path.getmtime(path))
        with api.build_kaggle_client() as kaggle:
            resp = kaggle.competitions.competition_api_client.start_submission_upload(req)
        json.dump({'url': resp.create_url, 'token': resp.token}, open(out, 'w'))
        print('upload session started; url saved to', out)
    elif cmd == 'finish':
        info = json.load(open(sys.argv[2]))
        message = sys.argv[3] if len(sys.argv) > 3 else 'invsqrt submission'
        from kaggle.api.kaggle_api_extended import ApiCreateSubmissionRequest
        api = client()
        req = ApiCreateSubmissionRequest()
        req.competition_name = COMP
        req.blob_file_tokens = info['token']
        req.submission_description = message
        with api.build_kaggle_client() as kaggle:
            resp = kaggle.competitions.competition_api_client.create_submission(req)
        print('submission created:', resp)
    else:
        raise SystemExit(f'unknown command {cmd}')


if __name__ == '__main__':
    main()
