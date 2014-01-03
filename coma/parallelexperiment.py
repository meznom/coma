from IPython.parallel import Client
import traceback
from .experiment import Experiment, ParameterSet

class ParallelExperiment(Experiment):
    def __init__(self, *args, **kwargs):
        profile = 'default'
        if kwargs.has_key('profile'):
            profile = kwargs['profile']
            del kwargs['profile']

        Experiment.__init__(self, *args, **kwargs)
        self.tasks = []
        self.pclient = Client(profile=profile)
        self.pview = self.pclient.load_balanced_view()

    def run(self, function=None):
        existing = self._get_existing_psets()
        todo = [p for p in self.psets if p not in existing]

        self.start()
        for p in todo:
            self.run_measurement(function, ParameterSet(self.pset_definition, p))
        
        while self.pview.wait(timeout=1) == False:
            self.save_measurements()
        self.pview.wait()
        self.save_measurements()
        
        self.end()
        self.save()

        return (len(todo),len(self.psets))

    def run_measurement(self, function, parameter_set):
        m = self.new_measurement()
        m.start()
        ar = self.pview.apply(function, parameter_set)
        self.tasks.append((m,ar,False))
        
    def save_measurements(self):
        for i,(m,ar,done) in enumerate(self.tasks):
            if (not ar.ready()) or done:
                continue
            if not ar.successful():
                print('Measurement {} was not successful.'.format(m.id))
                print('-'*60)
                try:
                    ar.get()
                except:
                    traceback.print_exc()
                print('-'*60)
                print('\n')
                self.tasks[i] = (m,ar,True)
                continue
            r = ar.get()
            m.end()
            m.save(r)
            # set done to True
            self.tasks[i] = (m,ar,True)
            # print('Saved measurement {}.'.format(m.id))
