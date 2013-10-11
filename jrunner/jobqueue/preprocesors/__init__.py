import importlib
import pickle as p

def process(task):
    """
        Unele task-uri au nevoie de procesare inante de a fi trimise catre MQ
        Spre exemplu, in momentul adaugarii unui app cu domeniu, task-urile
        create sunt dupa cum urmeaza:

        - adaugare app in baza de date cu status "pending"
        - adaugarea app serverelor in baza de date si adaugarea lor in task queue
        - adaugarea balancer-ului in baza de date si trimiterea lui in MQ
        - adaugarea APP-ului in MQ

        Balancer-ul depinde de AppServer pentru a afla portul backend-ului. Drept urmare
        informatiile din task-ul de adaugare a balancer-ului sunt incomplete pana la finalizarea
        task-urilor anterioare.

        Procesatorul va adauga informatiile lipsa inainte de a face push.
    """
    procesor = None
    try:
        procesor = importlib.import_module('jrunner.jobqueue.preprocesors.%s' % str(task.resource))
    except Exception as err:
        pass

    if procesor is None:
        return task

    return procesor.process(task)
