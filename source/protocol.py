"""课表 CalDAV 子集，资源和重复事件均为合成资料。"""
from xml.sax.saxutils import escape
import xml.etree.ElementTree as E
PREFIX='xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav"'
def xml(s,status=207):return status,{"Content-Type":"application/xml; charset=utf-8"},s
class Source:
    name="联合教学日历"
    def objects(self,cal):
        main="""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//合成校园//课表//ZH
BEGIN:VEVENT
UID:joint-class
DTSTAMP:20261101T000000Z
DTSTART;TZID=America/New_York:20261025T090000
DTEND;TZID=America/New_York:20261025T100000
RRULE:FREQ=WEEKLY;COUNT=5
RDATE;TZID=America/New_York:20261104T090000
EXDATE;TZID=America/New_York:20261122T090000
SUMMARY:联合软件实验
END:VEVENT
"""
        if self.stage>=1:
            main+="""BEGIN:VEVENT
UID:joint-class
RECURRENCE-ID;TZID=America/New_York:20261108T090000
DTSTART;TZID=America/New_York:20261115T150000
DTEND;TZID=America/New_York:20261115T160000
SUMMARY:联合软件实验调课
END:VEVENT
BEGIN:VEVENT
UID:joint-class
RECURRENCE-ID;TZID=America/New_York:20261115T090000
DTSTART;TZID=America/New_York:20261115T090000
STATUS:CANCELLED
END:VEVENT
"""
        main+="END:VCALENDAR\n"
        if cal=="east":
            main=main.replace("America/New_York","Asia/Shanghai").replace("联合软件实验","另一日历同UID课程")
        name="renamed.ics" if self.stage>=2 else "course.ics"
        return {} if self.stage>=3 else {f"/cal/{cal}/{name}":main.replace("\n","\r\n")}
    def response(self,href,data=None,status=200):
        if status==404:return f"<d:response><d:href>{href}</d:href><d:status>HTTP/1.1 404 Not Found</d:status></d:response>"
        return f'<d:response><d:href>{href}</d:href><d:propstat><d:prop><d:getetag>"{self.stage}-{href.rsplit("/",1)[-1]}"</d:getetag><c:calendar-data>{escape(data or "")}</c:calendar-data></d:prop><d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response>'
    def route(self,method,path,q,headers,body):
        parts=path.split("/")
        if len(parts)<3 or parts[1]!="cal" or parts[2] not in ["west","east"]:return 404,{},b""
        cal=parts[2];objects=self.objects(cal)
        if method=="GET":
            return (200,{"Content-Type":"text/calendar; charset=utf-8","ETag":f'"{self.stage}-{parts[-1]}"'},objects[path]) if path in objects else (404,{},b"")
        root=E.fromstring(body or b'<propfind xmlns="DAV:"/>')
        local=root.tag.split("}")[-1]
        token=f"urn:sync:{cal}:{self.stage}"
        if local=="sync-collection":
            old=root.findtext("{DAV:}sync-token","")
            if old and old!=f"urn:sync:{cal}:{self.stage-1}" and old!=token:
                return xml(f'<d:error {PREFIX}><d:valid-sync-token/></d:error>',403)
            changed=[]
            if old!=token:
                if self.stage==2:changed.append(self.response(f"/cal/{cal}/course.ics",status=404))
                if self.stage>=3:changed.append(self.response(f"/cal/{cal}/renamed.ics",status=404))
                changed += [self.response(k,v) for k,v in objects.items()]
            return xml(f'<d:multistatus {PREFIX}>'+"".join(changed)+f"<d:sync-token>{token}</d:sync-token></d:multistatus>")
        if local=="calendar-multiget":
            hrefs=[n.text for n in root.findall("{DAV:}href")]
            result="".join(self.response(k,objects[k]) if k in objects else self.response(k,status=404) for k in hrefs)
        elif local in ["calendar-query","propfind"]:
            # 查询允许保守多返回资源；保留全体例外，客户端决定实例窗口。
            result="".join(self.response(k,v) for k,v in objects.items())
        else:return xml(f'<d:error {PREFIX}><d:supported-report/></d:error>',400)
        return xml(f'<d:multistatus {PREFIX}>'+result+f"<d:sync-token>{token}</d:sync-token></d:multistatus>")
