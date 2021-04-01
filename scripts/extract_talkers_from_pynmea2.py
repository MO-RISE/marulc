import json

from pynmea2.nmea import TalkerSentence, ProprietarySentence

out = {
    "Talkers": dict(),
    "Proprietary": dict(),
}

# Talker sentences
for subclass in TalkerSentence.__subclasses__():
    try:
        name = subclass.__name__
        descr = (subclass.__doc__ or "").rstrip().lstrip()
        fields = []
        for field in subclass.fields:
            fields.append({
                "Id": field[1],
                "Description": field[0],
            })
        out["Talkers"][name] = {
            "Fields": fields,
            "Description": descr,
        }
    except AttributeError:
        pass

# Proprietary sentences
for manufacturer in ProprietarySentence.__subclasses__():
    name = manufacturer.__name__
    descr = (manufacturer.__doc__ or "").rstrip().lstrip()
    man = {
        "Decription": descr,
        "Sentences": dict(),
    }

    for sentence in manufacturer.__subclasses__():
        sent = sentence.__name__.replace(name, "")
        doc = (sentence.__doc__ or "").rstrip().lstrip()

        fields = []
        for field in sentence.fields:
            fields.append({
                "Id": field[1],
                "Description": field[0],
            })

        man["Sentences"][sent] = {
            "Fields": fields,
            "Description": doc
        }
    out["Proprietary"][name] = man

with open("talkers.json", "w") as f:
    json.dump(out, f, indent=4)