from tests.support import SourceCase
from zoneinfo import ZoneInfo
from datetime import datetime
import xml.etree.ElementTree as E
class Contract(SourceCase):
    def report(self,body,cal="west"):
        s,h,b=self.request("/cal/"+cal+"/","REPORT",body,{"Content-Type":"application/xml"})
        return s,E.fromstring(b)
    def test_calendar_query(self):
        s,t=self.report('<c:calendar-query xmlns:c="urn:ietf:params:xml:ns:caldav"/>')
        self.assertEqual(s,207);self.assertEqual(len(t.findall("{DAV:}response")),1)
    def test_full_resource_overrides(self):
        self.control(1)
        b=self.request("/cal/west/course.ics")[2].decode()
        self.assertIn("RECURRENCE-ID;TZID=America/New_York:20261108T090000",b)
        self.assertIn("DTSTART;TZID=America/New_York:20261115T150000",b)
        self.assertIn("STATUS:CANCELLED",b)
    def test_dst_offsets(self):
        z=ZoneInfo("America/New_York")
        self.assertNotEqual(datetime(2026,10,25,9,tzinfo=z).utcoffset(),datetime(2026,11,8,9,tzinfo=z).utcoffset())
    def test_calendar_scopes(self):
        w=self.request("/cal/west/course.ics")[2]
        e=self.request("/cal/east/course.ics")[2]
        self.assertIn(b"UID:joint-class",w);self.assertIn(b"UID:joint-class",e);self.assertNotEqual(w,e)
    def test_rename_sync(self):
        self.control(2)
        s,t=self.report('<d:sync-collection xmlns:d="DAV:"><d:sync-token>urn:sync:west:1</d:sync-token></d:sync-collection>')
        self.assertEqual(s,207)
        self.assertIn("404",E.tostring(t).decode());self.assertIn("renamed.ics",E.tostring(t).decode())
    def test_invalid_token(self):
        self.control(2)
        s,t=self.report('<d:sync-collection xmlns:d="DAV:"><d:sync-token>urn:sync:west:0</d:sync-token></d:sync-collection>')
        self.assertEqual(s,403);self.assertIsNotNone(t.find("{DAV:}valid-sync-token"))
    def test_multiget_missing(self):
        s,t=self.report('<c:calendar-multiget xmlns:c="urn:ietf:params:xml:ns:caldav" xmlns:d="DAV:"><d:href>/cal/west/no.ics</d:href></c:calendar-multiget>')
        self.assertIn("404",E.tostring(t).decode())
    def test_resource_delete(self):
        self.control(3)
        self.assertEqual(self.request("/cal/west/renamed.ics")[0],404)
        s,t=self.report('<d:sync-collection xmlns:d="DAV:"><d:sync-token>urn:sync:west:2</d:sync-token></d:sync-collection>')
        self.assertIn("404",E.tostring(t).decode())
