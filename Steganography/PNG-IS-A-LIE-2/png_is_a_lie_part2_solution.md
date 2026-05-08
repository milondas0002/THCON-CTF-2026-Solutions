# PNG is a lie (part 2/2) — Steganography Writeup

## Challenge information

**Challenge name:** PNG is a lie (part 2/2)

**Description:**

> Well, now we know for certain that something lies in this file. We have sent your image to an elite steganographer here at SNAFU.
>
> He has since become totally insane and keeps repeating that "the music's URL is the key"... do with this as you please.

The file for this challenge was the same file from **PNG is a lie (part 1/2)**.

---

## Final flag

```text
THC{Y'411_s0_r1Ckr0113D}
```

---

## Short summary

In part 1, the given `.thc` file was not a normal PNG directly. It contained many thumbs-up and thumbs-down emojis. The part 1 script treated:

```text
👍 = 1
👎 = 0
```

Then it grouped every 8 bits into one byte and rebuilt the real PNG file.

For part 2, I opened the extracted PNG in **StegSolve** and checked the bit planes. I found a QR-like pattern in the **RGB 3 planes bit 0 number plane**.

The QR code was not clean enough to scan directly. It had noise, broken parts, and damaged/stylized finder patterns. After cleaning and repairing the QR image, it decoded to a YouTube URL:

```text
https://www.youtube.com/watch?v=lpiB2wMc49g?flqg=THC{Y'411_s0_r1Ckr0113D}
```

The challenge hint said:

```text
the music's URL is the key
```

So the important part was not the video itself. The flag was hidden inside the URL after `flqg=`.

---

## Step 1: Rebuild the PNG from the `.thc` file

The script from part 1 reads the `.thc` file as text and collects only the emoji bits.

Basic idea:

```python
if ch == "👍":
    bit = 1
elif ch == "👎":
    bit = 0
```

After that, every 8 bits are converted into one byte. A PNG file is just bytes, so rebuilding the correct bytes gives us the real image.

Run the part 1 solver:

```bash
python3 solve.py
```

This gives:

```text
extracted.png
```

At this point, we have the real PNG image. Part 2 starts from this extracted PNG.

---

## Step 2: Open the image in StegSolve

I opened `extracted.png` using **StegSolve**.

```bash
java -jar stegsolve.jar
```

Then:

```text
File -> Open -> extracted.png
```

After opening the image, I used the arrow buttons or the bit-plane options to check different planes.

The important finding was:

```text
I analysed using StegSolve and found the QR at RGB 3 planes bit 0 number plane.
```

A QR-like pattern became visible there.

---

## What is a bit plane?

A normal RGB image has pixels. Each pixel has three color values:

```text
R = Red
G = Green
B = Blue
```

Each value is usually from `0` to `255`.

Example:

```text
R = 120
G = 45
B = 200
```

A computer stores these values in binary. Binary means only `0` and `1`.

For example:

```text
120 = 01111000
```

Each position in this binary number is called a **bit**.

The last bit is called **bit 0** or the **least significant bit**.

Example:

```text
01111000
       ^
       bit 0
```

Changing bit 0 changes the color value by only `1`. For example:

```text
120 -> 121
```

This small change is almost impossible to see with human eyes. That is why CTF authors often hide data in bit 0.

A **bit plane** means we view only one bit position from the whole image. Instead of looking at the normal colors, we only ask:

```text
Is bit 0 set or not?
```

If it is set, we show white. If it is not set, we show black.

That is how hidden images, text, or QR codes can appear.

---

## What does RGB 3 planes bit 0 mean?

When checking only the Red bit 0 plane, the QR pattern was present but not perfect.

When checking only the Green bit 0 plane, it was also visible.

When checking only the Blue bit 0 plane, it was also visible.

The better result came from combining the bit 0 data from all three channels:

```text
Red bit 0 OR Green bit 0 OR Blue bit 0
```

In simple words:

```text
If the hidden bit exists in Red OR Green OR Blue, keep it.
```

That makes the QR pattern stronger and easier to see.


## Step 3: Why the QR did not scan directly

At first, I tried to scan the QR directly from the bit plane.

It failed.

That happened because the QR was not a clean normal QR code. It had several problems:

### 1. Noise

Noise means extra random black or white pixels that do not belong to the QR code.

For a human, the QR shape was visible. But QR scanners are strict. Too much noise can stop the scanner from reading it.

### 2. Damaged finder patterns

A QR code has three big square markers in these corners:

```text
Top-left
Top-right
Bottom-left
```

These are called **finder patterns**.

They help the scanner understand:

```text
Where does the QR start?
What is its angle?
How large are the QR blocks?
```

In this challenge, those corner markers were not clean. Some parts looked circular/stylized instead of perfect QR finder squares. Because of that, scanners could not detect the QR correctly.

### 3. No proper quiet zone

A QR code needs an empty white border around it. This border is called the **quiet zone**.

If the QR touches other noisy pixels or the image edge, many scanners fail.

### 4. Broken modules

The small black and white squares inside a QR are called **modules**.

Some modules were broken or unclear. A scanner expects a clean grid, so broken modules make decoding harder.

---

## Step 4: Trial and error used to clean the QR

I did not get the flag in one try. I had to try multiple cleaning methods.

### Try 1: Scan the raw bit plane

I first tried to scan the raw QR found in StegSolve.

Result:

```text
Failed
```

Reason:

```text
Too noisy and finder patterns were not clean.
```

---

### Try 2: Check individual color channels

I checked:

```text
Red bit 0
Green bit 0
Blue bit 0
```

The QR was visible in them, but none of them alone was clean enough.

Result:

```text
Still failed
```

Reason:

```text
Each channel had only part of the useful QR data or still had too much noise.
```

---

### Try 3: Combine RGB bit 0 planes

Then I combined the bit 0 plane of Red, Green, and Blue together.

Logic:

```text
R0 OR G0 OR B0
```

This made the QR clearer.

Result:

```text
Better QR shape, but scanner still failed.
```

Reason:

```text
The QR was clearer, but the corner finder patterns and module grid were still not scanner-friendly.
```

---

### Try 4: Invert black and white

Sometimes QR scanners expect black modules on a white background. If the colors are reversed, scanning can fail.

So I tried both:

```text
Normal image
Inverted image
```

Result:

```text
Still not enough
```

Reason:

```text
The main problem was not only color. The QR structure was damaged/noisy.
```

---

### Try 5: Add a white border / quiet zone

I added a clean white border around the QR.

This is important because scanners need some empty space around the QR.

Result:

```text
Scanner detection improved, but still not fully decoded.
```

---

### Try 6: Thresholding

Thresholding means converting a gray/noisy image into a pure black-and-white image.

Example:

```text
If pixel is dark enough -> black
If pixel is bright enough -> white
```

I tried multiple threshold values.

For example:

```text
15, 25, 35, 45, 55
```

Result:

```text
Some values removed useful QR parts.
Some values kept too much noise.
Threshold around 35 gave a better result.
```

This is why trial and error was needed.

---

### Try 7: Rebuild the QR grid

A QR code is not a normal picture. It is a square grid.

Each small square in the QR should be either black or white.

So instead of trusting every noisy pixel, I treated the QR as a grid and cleaned it like this:

1. Crop the QR area.
2. Divide the QR into equal square cells/modules.
3. For each cell, check whether most pixels are black or white.
4. Replace the whole cell with one clean black or white square.

This is called **grid reconstruction**.

Simple explanation:

```text
Instead of keeping messy pixels, we rebuild the QR as clean blocks.
```

---

### Try 8: Repair the finder patterns

The final important fix was repairing the three QR corner markers.

A normal QR finder pattern looks like this in grid form:

```text
1111111
1000001
1011101
1011101
1011101
1000001
1111111
```

Here:

```text
1 = black
0 = white
```

The QR from the image had damaged/stylized finder patterns. So I repaired them into normal QR finder patterns at:

```text
Top-left
Top-right
Bottom-left
```

After this repair, the QR scanner could finally understand the code.

---


## Step 5: Decode the cleaned QR

After cleaning and repairing the QR, it decoded to:

```text
https://www.youtube.com/watch?v=lpiB2wMc49g?flqg=THC{Y'411_s0_r1Ckr0113D}
```

At first, this only looks like a YouTube music URL.

But the challenge hint said:

```text
the music's URL is the key
```

So the important thing is the URL itself.

Inside the URL, there is this part:

```text
flqg=THC{Y'411_s0_r1Ckr0113D}
```

This means the flag is stored after `flqg=`.

So the flag is:

```text
THC{Y'411_s0_r1Ckr0113D}
```

---

## Beginner-friendly explanation of the full attack path

This challenge had two layers.

### Layer 1: Fake file format

The file extension was `.thc`, not `.png`.

But the file secretly contained bits using emojis.

The part 1 script converted emoji bits into bytes and recovered the PNG.

### Layer 2: Hidden QR inside image pixels

The recovered PNG looked normal, but its least significant bits contained another image.

Using StegSolve, we checked bit planes and found a QR in the RGB bit 0 plane.

### Layer 3: Dirty QR cleanup

The QR was visible to humans but not readable by scanners.

So we had to:

```text
Extract bit 0 data
Combine RGB planes
Convert to black and white
Try inversion
Add quiet zone
Clean noise
Rebuild QR blocks
Repair finder patterns
Scan again
```

Finally, the QR gave a YouTube URL, and the flag was inside that URL.

---

## Important terms

### Steganography

Steganography means hiding data inside another file.

Example:

```text
Hiding text inside an image
Hiding a ZIP inside a PNG
Hiding a QR code inside pixel bits
```

The file may look normal, but secret data is inside it.

### LSB

LSB means **Least Significant Bit**.

It is the last bit of a binary number.

Changing it makes only a tiny change to the color, so humans usually cannot notice it.

That makes LSB useful for hiding data in images.

### Bit plane

A bit plane is a view of only one bit from every pixel.

If hidden data is placed in a specific bit, checking that bit plane can reveal the secret.

### RGB

RGB means:

```text
Red
Green
Blue
```

These three color channels create the final image color.

### QR finder pattern

Finder patterns are the three big corner markers of a QR code.

They help QR scanners locate and align the QR code.

If these patterns are damaged, the QR may not scan even if the data is mostly correct.

### Quiet zone

The quiet zone is the empty white border around a QR code.

It helps the scanner separate the QR from the background.

Without a quiet zone, scanners often fail.

### Thresholding

Thresholding means turning a gray image into a pure black-and-white image.

It helps remove weak noise and makes QR modules cleaner.

---

## Conclusion

The main hint was:

```text
the music's URL is the key
```

This told us that after finding the QR, we should focus on the decoded URL.

The QR was hidden in the RGB least significant bit plane of the PNG. Because the QR was noisy and damaged, it needed cleaning and finder-pattern repair before scanning.

Decoded URL:

```text
https://www.youtube.com/watch?v=lpiB2wMc49g?flqg=THC{Y'411_s0_r1Ckr0113D}
```

Final flag:

```text
THC{Y'411_s0_r1Ckr0113D}
```
