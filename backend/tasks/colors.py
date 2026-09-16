PERSON_COLORS = [
    "#B5476B",
    "#2E6A8E",
    "#7C4FA0",
    "#C97C3D",
    "#3D8FC9",
    "#4FA36B",
    "#B0538A",
    "#5A6FB0",
    "#C9A23D",
    "#3DC9A0",
    "#C9503D",
]


def person_color(index):
    return PERSON_COLORS[index % len(PERSON_COLORS)]
