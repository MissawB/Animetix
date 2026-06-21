class LazyClass:
    """Résout paresseusement une classe `module.ClassName` au premier appel.

    Évite d'importer (et donc de charger) les services lourds au démarrage : la
    classe n'est importée qu'à la première instanciation par le conteneur DI.
    Partagé par tous les conteneurs (`infrastructure`, `persistence`, `inference`,
    `agentic`, `core_services`).
    """

    def __init__(self, module_name, class_name):
        self.module_name = module_name
        self.class_name = class_name
        self._class = None

    def __call__(self, *args, **kwargs):
        if self._class is None:
            import importlib

            module = importlib.import_module(self.module_name)
            self._class = getattr(module, self.class_name)
        return self._class(*args, **kwargs)
