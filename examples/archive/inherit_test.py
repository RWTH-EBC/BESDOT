
class Human(object):
    def __init__(self, name):
        self.name = name


class Man(Human):
    def __init__(self, name):
        super().__init__(name)

    def say(self):
        print('im a man')


class Student(Human):
    def __init__(self, name):
        super().__init__(name)

    def say(self):
        print('im a student')


class MaleStudent(Man, Student):
    def __init__(self, name):
        super().__init__(name)


class StudentMale(Student, Man):
    def __init__(self, name):
        super().__init__(name)


if __name__ == '__main__':
    xiaomin = MaleStudent('xiaomin')
    xiaomin.say()
    # output: im a man

    david = StudentMale('david')
    david.say()
    # output: im a student
