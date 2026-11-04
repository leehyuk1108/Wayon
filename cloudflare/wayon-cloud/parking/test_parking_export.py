import copy
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

import parking_export as p
from test_parking_scene import frames, reading


def record():
    return {'jobId':'a'*32, 'deviceId':'car-a', 'eventId':'park-a', 'parkedAt':'2026-01-01T00:00:00Z',
            'status':'completed', 'error':'private', 'result':{
                'analysis':{'readings':[reading()], 'exactParkingSpotKnown':False},
                'frames':frames(), 'usage':{'private':'not transmitted'}}}


class Publisher(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.service = Mock()
        self.service.latest.return_value = record()
        self.factory = patch.object(p, 'load_settings', return_value=('https://example.invalid', 'private-token', 'car-a', 0))
        self.factory.start()
        self.addCleanup(self.factory.stop)
        self.publisher = p.ParkingExport(self.service, Path(self.tmp.name))
        self.publisher.clock = lambda: 2000000000
        self.publisher.opener = Mock()
        self.success()

    def success(self):
        response = Mock(status=200)
        response.read.return_value = b'{"ok":true,"stored":true}'
        self.publisher.opener.open.return_value.__enter__ = Mock(return_value=response)
        self.publisher.opener.open.return_value.__exit__ = Mock(return_value=False)

    def test_changed_only_restart_and_daily_refresh(self):
        self.publisher.publish()
        self.publisher.publish()
        self.assertEqual(self.publisher.opener.open.call_count, 1)
        args, kwargs = self.publisher.opener.open.call_args
        payload = json.loads(args[0].data)
        self.assertEqual(args[0].full_url, 'https://example.invalid/api/parking/display')
        self.assertEqual(kwargs['timeout'], 5)
        self.assertEqual(payload['deviceId'], 'car-a')
        self.assertNotIn('error', payload['observation'])
        self.assertNotIn('usage', payload['observation']['result'])
        restarted = p.ParkingExport(self.service, Path(self.tmp.name))
        restarted.clock = self.publisher.clock
        restarted.opener = Mock()
        restarted.publish()
        restarted.opener.open.assert_not_called()
        self.publisher.clock = lambda: 2000086400
        self.publisher.publish()
        self.assertEqual(self.publisher.opener.open.call_count, 2)
        self.assertEqual(json.loads(self.publisher.opener.open.call_args.args[0].data)['generatedAt'], payload['generatedAt'])
        self.service.latest.return_value = {**record(), 'status':'failed', 'result':None}
        self.publisher.publish()
        sent = json.loads(self.publisher.opener.open.call_args.args[0].data)
        self.assertEqual(sent['observation']['status'], 'failed')
        self.assertIsNone(sent['observation']['result'])

    def test_failed_post_keeps_ack_and_backs_off(self):
        self.publisher.publish()
        previous = copy.deepcopy(self.publisher.last)
        self.service.latest.return_value = {**record(), 'status':'failed', 'result':None}
        self.publisher.opener.open.side_effect = OSError('private failure')
        self.publisher.publish()
        self.assertEqual(self.publisher.last, previous)
        self.assertEqual(self.publisher.next_attempt, 2000000060)
        with patch.object(p.threading, 'Thread') as worker:
            self.assertFalse(self.publisher.update())
            worker.assert_not_called()
        self.assertFalse(self.publisher.running)

    def test_scope_and_oversized_ack_fail_closed(self):
        self.service.latest.return_value['deviceId'] = 'car-b'
        self.publisher.publish()
        self.publisher.opener.open.assert_not_called()
        self.service.latest.return_value = record()
        response = Mock(status=200)
        response.read.return_value = b'x'*8193
        self.publisher.opener.open.return_value.__enter__.return_value = response
        self.publisher.publish()
        self.assertEqual(self.publisher.last, {})

    def test_one_thread_and_minimum_cadence(self):
        with patch.object(p.threading, 'Thread') as worker:
            self.assertTrue(self.publisher.update())
            self.assertFalse(self.publisher.update())
            self.assertEqual(worker.call_count, 1)
        self.publisher.running = False
        self.assertFalse(self.publisher.update())

    def test_failed_thread_creation_recovers_without_any_post(self):
        with patch.object(p.threading, 'Thread') as worker:
            worker.return_value.start.side_effect = RuntimeError('thread unavailable')
            with self.assertRaises(RuntimeError): self.publisher.update()
        self.assertFalse(self.publisher.running)
        self.publisher.opener.open.assert_not_called()

    def test_export_does_not_mutate_job_and_cannot_include_image_bytes(self):
        source = record()
        source['result']['frames'][0]['bytes'] = b'private raw image'
        before = copy.deepcopy(source)
        display = p.display_observation(source)
        self.assertEqual(source, before)
        self.assertNotIn('bytes', display['result']['frames'][0])
        self.service.db.execute.assert_not_called()
        self.service.parking_notify.assert_not_called()

    def test_generation_survives_failed_ack_restart_and_clock_regression(self):
        self.publisher.opener.open.side_effect = OSError('network')
        self.publisher.publish()
        original = json.loads(self.publisher.opener.open.call_args.args[0].data)['generatedAt']
        restarted = p.ParkingExport(self.service, Path(self.tmp.name))
        restarted.opener = self.publisher.opener
        restarted.clock = lambda: 1999999000
        restarted.publish()
        self.assertEqual(json.loads(restarted.opener.open.call_args.args[0].data)['generatedAt'], original)
        self.service.latest.return_value['status'] = 'failed'
        self.service.latest.return_value['result'] = None
        restarted.publish()
        self.assertGreater(json.loads(restarted.opener.open.call_args.args[0].data)['generatedAt'], original)

    def test_nonparking_test_events_never_publish(self):
        for event in ('snapshot-1', 'test-1', 'simulation-1', 'replay-1'):
            self.service.latest.return_value['eventId'] = event
            self.publisher.publish()
        self.publisher.opener.open.assert_not_called()
        self.assertEqual(self.publisher.status()['failures'], 4)


if __name__ == '__main__':
    unittest.main()
