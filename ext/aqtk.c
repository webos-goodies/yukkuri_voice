#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <structmember.h>
#include <AquesTalk.h>
#include <AqKanji2Koe.h>

#define METHOD_DEF(_name, _fn, _doc) \
  { (_name), ((PyCFunction)(void(*)(void))(_fn)), METH_VARARGS | METH_KEYWORDS, (_doc) }

typedef struct _StrLongPair {
  const char* name;
  long value;
} StrLongPair;

const StrLongPair ModuleLongs[] =
{
  { "gVoice_F1", 0 },
  { "gVoice_F2", 1 },
  { "gVoice_F3", 2 },
  { "gVoice_M1", 3 },
  { "gVoice_M2", 4 },
  { "gVoice_R1", 5 },
  { "gVoice_R2", 6 }
};

static PyObject* AqtkError;

static PyObject* raise_aqtk_error(int code)
{
  PyErr_Format(AqtkError, "AquesTalk API error: %d", code);
  return NULL;
}

static PyObject* aqtk_synthe(PyObject* self, PyObject* args, PyObject* kwargs)
{
  const char* koe = NULL;
  int type = 0, bas = -1, spd = -1, vol = -1, pit = -1, acc = -1, lmd = -1, fsc = -1;

  static char* kwlist[] = { "", "type", "bas", "spd", "vol", "pit", "acc", "lmd", "fsc", NULL };
  if(!PyArg_ParseTupleAndKeywords(args, kwargs, "s|iiiiiiii", kwlist,
                                  &koe, &type, &bas, &spd, &vol, &pit, &acc, &lmd, &fsc)) {
    return NULL;
  }

  AQTK_VOICE pParam;
  switch(type) {
  case 0: pParam = gVoice_F1; break;
  case 1: pParam = gVoice_F2; break;
  case 2: pParam = gVoice_F3; break;
  case 3: pParam = gVoice_M1; break;
  case 4: pParam = gVoice_M2; break;
  case 5: pParam = gVoice_R1; break;
  case 6: pParam = gVoice_R2; break;
  default:
    PyErr_Format(PyExc_ValueError, "Invalid type %d", type);
    return NULL;
  }

  if(bas >= 0) { pParam.bas = bas; }
  if(spd >= 0) { pParam.spd = spd; }
  if(vol >= 0) { pParam.vol = vol; }
  if(pit >= 0) { pParam.pit = pit; }
  if(acc >= 0) { pParam.acc = acc; }
  if(lmd >= 0) { pParam.lmd = lmd; }
  if(fsc >= 0) { pParam.fsc = fsc; }

  int wavSize = 0;
  unsigned char* wav = AquesTalk_Synthe_Utf8(&pParam, koe, &wavSize);
  if(!wav) {
    return raise_aqtk_error(wavSize);
  }

  PyObject* rv = Py_BuildValue("y#", (const char*)wav, (Py_ssize_t)wavSize);
  AquesTalk_FreeWave(wav);
  if(!rv) {
    return NULL;
  }

  return rv;
}

static PyObject* aqtk_set_license_key(PyObject* self, PyObject* args, PyObject* kwargs)
{
  const char* type = NULL;
  const char* key  = NULL;

  static char* kwlist[] = { "type", "key", NULL };
  if(!PyArg_ParseTupleAndKeywords(args, kwargs, "ss", kwlist, &type, &key)) {
    return NULL;
  }

  int result = 0;
  if(strcmp("aquestalk_dev", type) == 0) {
    result = AquesTalk_SetDevKey(key);
  } else if(strcmp("aquestalk_usr", type) == 0) {
    result = AquesTalk_SetUsrKey(key);
  } else if(strcmp("kanji2koe_dev", type) == 0) {
    result = AqKanji2Koe_SetDevKey(key);
  } else {
    PyErr_Format(PyExc_ValueError, "Invalid license type %s", key);
    return NULL;
  }

  return PyLong_FromLong(result);
}

typedef struct {
  PyObject_HEAD
  void* aq_converter;
} AqKanji2KoeObject;

static int AqKanji2Koe_init(AqKanji2KoeObject* self, PyObject* args, PyObject* kwargs)
{
  static char* kwlist[] = { "path", NULL };
  const char* path = NULL;

  if(!PyArg_ParseTupleAndKeywords(args, kwargs, "s", kwlist, &path)) {
    return -1;
  }

  if(!self->aq_converter) {
    int errcode = 0;
    self->aq_converter = AqKanji2Koe_Create(path, &errcode);
    if(!self->aq_converter) {
      raise_aqtk_error(errcode);
      return -1;
    }
  }

  return 0;
}

static void AqKanji2Koe_dealloc(AqKanji2KoeObject* self)
{
  if(self->aq_converter) {
    AqKanji2Koe_Release(self->aq_converter);
    self->aq_converter = NULL;
  }

  Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject* AqKanji2Koe_convert(AqKanji2KoeObject* self, PyObject* args, PyObject* kwargs)
{
  static char* kwlist[] = { "kanji", NULL };
  const char* kanji = NULL;
  PyObject* rv = NULL;

  if(!PyArg_ParseTupleAndKeywords(args, kwargs, "s", kwlist, &kanji)) {
    return NULL;
  }

  Py_ssize_t bufSize = strlen(kanji) * 4;
  char* koe = malloc(bufSize + 16);
  if(!koe) {
    return PyErr_NoMemory();
  }

  if(!self->aq_converter) {
    PyErr_SetString(PyExc_RuntimeError, "No converter initialized");
    goto error;
  }

  int errcode = AqKanji2Koe_Convert(self->aq_converter, kanji, koe, bufSize);
  if(errcode != 0) {
    raise_aqtk_error(errcode);
    goto error;
  }

  rv = PyUnicode_FromString(koe);
error:
  if(koe) {
    free(koe);
  }
  return rv;
}

static PyMethodDef AqKanji2Koe_methods[] =
{
  METHOD_DEF("convert", AqKanji2Koe_convert, "Convert a kanji string to a koe string"),
  { NULL } /* Sentinel */
};

static PyTypeObject AqKanji2KoeType =
{
  PyVarObject_HEAD_INIT(NULL, 0)
  .tp_name = "aqtk.AqKanji2Koe",
  .tp_doc = "AqKanji2Koe wrapper",
  .tp_basicsize = sizeof(AqKanji2KoeObject),
  .tp_itemsize = 0,
  .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
  .tp_new = PyType_GenericNew,
  .tp_init = (initproc)AqKanji2Koe_init,
  .tp_dealloc = (destructor)AqKanji2Koe_dealloc,
  .tp_methods = AqKanji2Koe_methods,
};

static PyMethodDef AqtkMethods[] =
{
  METHOD_DEF("synthe",          aqtk_synthe, "Generate .wav"),
  METHOD_DEF("set_license_key", aqtk_set_license_key, "Set license key"),
  { NULL, NULL, 0, NULL } /* Sentinel */
};

static struct PyModuleDef aqtkmodule =
{
  PyModuleDef_HEAD_INIT,
  "aqtk",
  NULL,
  -1,
  AqtkMethods
};

PyMODINIT_FUNC PyInit_aqtk(void)
{
  if(PyType_Ready(&AqKanji2KoeType) < 0) {
    return NULL;
  }

  PyObject* m = PyModule_Create(&aqtkmodule);
  if(!m) {
    return NULL;
  }

  for(unsigned long i = 0 ; i < sizeof(ModuleLongs) / sizeof(ModuleLongs[0]) ; i++) {
    if(PyModule_AddIntConstant(m, ModuleLongs[i].name, ModuleLongs[i].value) < 0) {
      goto error;
    }
  }

  Py_INCREF(&AqKanji2KoeType);
  if(PyModule_AddObject(m, "AqKanji2Koe", (PyObject*)&AqKanji2KoeType) < 0) {
    Py_DECREF(&AqKanji2KoeType);
    goto error;
  }

  AqtkError = PyErr_NewException("aqtk.AqtkError", NULL, NULL);
  Py_XINCREF(AqtkError);
  if(PyModule_AddObject(m, "AqtkError", AqtkError) < 0) {
    Py_XDECREF(AqtkError);
    Py_CLEAR(AqtkError);
    goto error;
  }

  return m;

error:
  Py_DECREF(m);
  return NULL;
}
