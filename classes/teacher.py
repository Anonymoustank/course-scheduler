from __future__ import annotations
from typing import TYPE_CHECKING, List
from pulp import LpVariable, LpAffineExpression, value
from .schedule import Schedule
from .course import CourseType, Section
from utils import summation
from .individual import Individual
if TYPE_CHECKING:
    from .course import Course
    
class Teacher(Individual):
    __slots__ = ["_tag", "_allCourses", "_qualifications", "_openPeriods"]
    def __init__(self, tag: int, allCourses: List[str]):
        super().__init__(tag, allCourses)
        self._qualifications = []
        self._openPeriods = []
    
    def addQualification(self, qual: Course):
        if qual not in self._qualifications:
            self._qualifications.append(qual)
    
    def remQualification(self, qual: Course):
        if qual in self._qualifications:
            self._qualifications.remove(qual)

    def addQualifications(self, qualifications: List[Course]):
        for q in qualifications:
            self.addQualification(q)
    
    def addOpenPeriod(self, period: int):
        if period not in self._openPeriods:
            self._openPeriods.append(period)
    
    def remOpenPeriod(self, period: int):
        if period in self._openPeriods:
            self._openPeriods.remove(period)

    def isQualified(self, courseCode: str) -> bool:
        """
        Returns whether a teacher is qualified for a particular courseCode.
        """
        
        return (courseCode in self._qualifications)
    
    def getOpenPeriods(self) -> List[int]:
        """
        Returns open periods numbers.
        """

        return self.openPeriods
    
    def isOpen(self, period: int) -> bool:
        """
        Returns whether a particular period is open.
        """

        return (period in self.openPeriods)

    def addSection(self, newSection: Section):
        """
        Adds a section to the schedule.
        """

        res = self._schedule.addSection(newSection)
        if res:
            self._openPeriods.remove(newSection.period)
            self.addToSection(newSection)
    
    def removeSection(self, section: Section):
        """
        Removes a section from the schedule.
        """

        self._schedule.removeSection(section)
        section.instructor = None
        self.openPeriods.append(section.period)
        self.openPeriods.sort()
    
    def getQualified(self):
        """
        Yields whether or not teacher is qualified for each class teaching.
        """

        currScheduleVals = list(self.schedule.getSections().values())
        for section in currScheduleVals:
            yield (section == None or self.isQualified(section.courseCode))
    
    def getQualificationVector(self) -> List[int]:
        """
        Returns (eager) of the teacher's qualifications
        """
        vector = [0] * len(self._allCourses)
        for course in self._qualifications:
            index = self._allCourses.index(course)
            vector[index] = 1
        return vector
    
    def getConstraints(self):
        """
        Lazily generate all constraints by calling other constraint generator
        methods.
        """

        for c in super().getConstraints():
            yield c

        for c in self.getQualifiedTeachingConstraints():
            yield c


    def getQualifiedTeachingConstraints(self):
        """
        Lazily generate constraints ensuring this teacher only teaches sections
        that they are qualified to teach.
        """

        for course in self._allCourses:
            isQualified = 0
            if course in self._qualifications:
                isQualified = 1
            
            varList = []
            for period in range(self._schedule.periods):
                variable = self._schedule._lpVars[period][int(course._courseCode)]
                varList.append(variable)
            sumOfVariables = summation(varList)

            yield sumOfVariables <= isQualified
    
    def addToSection(self, section):
        section.changeInstructor(self)
        self._schedule.addSection(section)
    
    def getOpenScore(self) -> int:
        """
        Returns number of off periods
        """
        return len(self.openPeriods)
