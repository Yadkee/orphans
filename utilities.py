#! python3


def blit_text(surface, font, pos, text, fontColor, backgroundColor=None,
              size=None, anchor="NW", fill=True):
    antialiasing = True
    renderedFont = font.render(text, antialiasing, fontColor, backgroundColor)
    if size is not None:
        if backgroundColor is not None and fill:
            surface.fill(backgroundColor, (pos, size))
        textRect = renderedFont.get_rect()
        # North, South and Center
        if "N" in anchor:
            textRect.top = pos[1]
        elif "S" in anchor:
            textRect.bottom = pos[1] + size[1]
        else:
            textRect.centery = pos[1] + size[1] // 2
        # West, East and Center
        if "W" in anchor:
            textRect.left = pos[0]
        elif "E" in anchor:
            textRect.right = pos[0] + size[0]
        else:
            textRect.centerx = pos[0] + size[0] // 2
        surface.blit(renderedFont, textRect)
    else:
        surface.blit(renderedFont, pos)
