from celery.backends.mongodb import MongoBackend
from datetime import datetime
from kombu.utils.encoding import ensure_bytes

class ExtendedMongoBackend(MongoBackend):
    """
        Extended MongoDB backend for Celery task results to include
        the task name in the results stored in Mongo
    """
    
    def _get_result_meta(self, result,
                         state, traceback, request, format_date=True,
                         encode=False):
        if state in self.READY_STATES:
            date_done = datetime.utcnow()
            if format_date:
                date_done = date_done.isoformat()
        else:
            date_done = None

        meta = {
            'status': state,
            'result': result,
            'traceback': traceback,
            'children': self.current_task_children(request),
            'date_done': date_done,
            'task': getattr(request, 'task', None)
        }

        if request and getattr(request, 'group', None):
            meta['group_id'] = request.group
        if request and getattr(request, 'parent_id', None):
            meta['parent_id'] = request.parent_id

        if self.app.conf.find_value_for_key('extended', 'result'):
            if request:
                request_meta = {
                    'name': getattr(request, 'task', None),
                    'args': getattr(request, 'args', None),
                    'kwargs': getattr(request, 'kwargs', None),
                    'worker': getattr(request, 'hostname', None),
                    'retries': getattr(request, 'retries', None),
                    'queue': request.delivery_info.get('routing_key')
                    if hasattr(request, 'delivery_info') and
                    request.delivery_info else None,
                }
                if getattr(request, 'stamps', None):
                    request_meta['stamped_headers'] = request.stamped_headers
                    request_meta.update(request.stamps)

                if encode:
                    # args and kwargs need to be encoded properly before saving
                    encode_needed_fields = {"args", "kwargs"}
                    for field in encode_needed_fields:
                        value = request_meta[field]
                        encoded_value = self.encode(value)
                        request_meta[field] = ensure_bytes(encoded_value)

                meta.update(request_meta)

        return meta
