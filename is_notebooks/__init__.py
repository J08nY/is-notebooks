from dataclasses import dataclass
from abc import ABC
from typing import ClassVar, List, Optional

import requests
from bs4 import BeautifulSoup


@dataclass
class Faculty:
    en_name: str
    cz_name: str
    en_short: str
    cz_short: str
    id: int


class University(ABC):
    API_URL: ClassVar[str]
    FACULTIES: ClassVar[List[Faculty]]

    def get_faculty_by_en_short(self, en_short) -> Optional[Faculty]:
        for f in self.FACULTIES:
            if f.en_short == en_short:
                return f
        return None

    def get_faculty_by_cz_short(self, cz_short) -> Optional[Faculty]:
        for f in self.FACULTIES:
            if f.cz_short == cz_short:
                return f
        return None


class MasarykUniversity(University):
    API_URL = "https://is.muni.cz/export/pb_blok_api"
    FACULTIES = [
        Faculty("Faculty of Medicine", "Lékařská fakulta", "medicine", "LF", 1411),
        Faculty("Faculty of Pharmacy", "Farmaceutická fakulta", "pharmacy", "FaF", 1416),
        Faculty("Faculty of Arts", "Filozofická fakulta", "arts", "FF", 1421),
        Faculty("Faculty of Social Studies", "Fakulta sociálních studií", "social", "FSS", 1423),
        Faculty("Faculty of Science", "Přírodovědecká fakulta", "science", "PřF", 1431),
        Faculty("Faculty of Informatics", "Fakulta informatiky", "informatics", "FI", 1433),
        Faculty("Faculty of Education", "Pedagogická fakulta", "education", "PdF", 1441),
        Faculty("Faculty of Sports Studies", "Fakulta sportovních studií", "sports", "FSpS", 1451),
        Faculty("Faculty of Economics and Administration", "Ekonomicko-správní fakulta", "economics", "ESF", 1456)
    ]


class APIResponse:
    response: requests.Response
    xml: BeautifulSoup

    def __init__(self, response: requests.Response):
        self.response = response
        self.xml = BeautifulSoup(response.content, "lxml-xml")


class API:
    university: University
    faculty: Faculty
    course: str
    api_key: str

    def __init__(self, university: University, faculty: Faculty, course: str, api_key: str):
        self.university = university
        self.faculty = faculty
        self.course = course
        self.api_key = api_key
        self.params = {"klic": self.api_key,
                       "fakulta": self.faculty.id,
                       "kod": self.course}

    def _get(self, params) -> APIResponse:
        kw_params = {param[0]: param[1] for param in params} + self.params
        resp = requests.get(self.university.API_URL, params=kw_params)
        return APIResponse(resp)

    def info(self) -> APIResponse:
        return self._get([("operace", "predmet-info")])

    def students(self, registered: bool = False, ended_study: bool = False,
                 inactive_study: bool = False) -> APIResponse:
        params = [("operace", "predmet-seznam")]
        if registered:
            params.append(("zareg", "a"))
        if ended_study:
            params.append(("vcukonc", "a"))
        if inactive_study:
            params.append(("vcneaktiv", "a"))
        return self._get(params)

    def seminar_students(self, *seminars: str, ended_study: bool = False,
                         inactive_study: bool = False) -> APIResponse:
        params = [("operace", "seminar-seznam")]
        for seminar in seminars:
            params.append(("seminar", seminar))
        if ended_study:
            params.append(("vcukonc", "a"))
        if inactive_study:
            params.append(("vcneaktiv", "a"))
        return self._get(params)

    def seminar_teachers(self, *seminars: str) -> APIResponse:
        params = [("operace", "seminar-cvicici-seznam")]
        for seminar in seminars:
            params.append(("seminar", seminar))
        return self._get(params)

    def notebooks(self) -> APIResponse:
        return self._get([("operace", "bloky-seznam")])

    def new_notebook(self, name: str, shortname: str, visible: bool = False,
                     no_fill_in: bool = False, statistics: bool = False) -> APIResponse:
        params = [("operace", "blok-novy"), ("jmeno", name), ("zkratka", shortname),
                  ("nahlizi", "a" if visible else "n"), ("nedoplnovat", "a" if no_fill_in else "n"),
                  ("statistika", "a" if statistics else "n")]
        return self._get(params)

    def notebook(self, shortname: str, *ucos: int) -> APIResponse:
        params = [("operace", "blok-dej-obsah"), ("zkratka", shortname)]
        for uco in ucos:
            params.append(("uco", str(uco)))
        return self._get(params)

    def edit_notebook(self, shortname: str, uco: int, content: str, last_edited: str = None,
                      overwrite: bool = False) -> APIResponse:
        params = [("operace", "blok-pis-student-obsah"), ("zkratka", shortname), ("uco", str(uco)),
                  ("obsah", content), ("prepis", "a" if overwrite else "n")]
        if last_edited is not None:
            params.append(("poslzmeneno", last_edited))
        return self._get(params)

    def exam_dates(self, ended_study: bool = False, inactive_study: bool = False) -> APIResponse:
        params = [("operace", "terminy-seznam")]
        if ended_study:
            params.append(("vcukonc", "a"))
        if inactive_study:
            params.append(("vcneaktiv", "a"))
        return self._get(params)
