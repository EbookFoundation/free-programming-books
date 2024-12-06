# ML-Machine-Learning

<p align="right">
  <img src="https://github.com/akashdip2001/ML-Machine-Learning/assets/81384987/dff140e6-3c24-4430-96b6-48877e6c98b9" alt="Pandas Logo" width="500" />
</p>

| GitHub Repo |🍭 [ML](https://github.com/akashdip2001/ML-Machine-Learning) 🍭|🐥 [Pandas](https://github.com/akashdip2001/ML-Machine-Learning/tree/main/pandas) 🐥|❌ [numPy](https://github.com/akashdip2001/ML-Machine-Learning/tree/main/numPy) ❌|
|-------------------- |-------------------- |-------------------- |-------------------- |


| WebSite => |🍭 [ML](https://akashdip2001.github.io/ML-Machine-Learning/) 🍭|🐥 [Pandas](https://akashdip2001.github.io/ML-Machine-Learning/pandas.html) 🐥|❌ [numPy](https://akashdip2001.github.io/ML-Machine-Learning/numPy.html) ❌|
|-------------------- |-------------------- |-------------------- |-------------------- |

---

![ml](https://github.com/akashdip2001/ML-Machine-Learning/raw/main/ML/img/ml_roadmap01.jpg)

![ml](https://github.com/akashdip2001/ML-Machine-Learning/raw/main/ML/img/ml_roadmap02.jpg)

# Jupyter Notebook // JupyterLab // .ipynb

### Command Mode Shortcuts (press Esc to activate)
- **A**: Insert cell above
- **B**: Insert cell below
- **D, D** (press D twice): Delete selected cell
- **Y**: Change cell to code mode
- **M**: Change cell to markdown mode
- **Shift + Arrow**: Select multiple cells
- **Shift + M**: Merge selected cells
- **Ctrl + Enter**: Run selected cell
- **Shift + Enter**: Run cell and select below
- **Alt + Enter**: Run cell and insert new cell below

### Edit Mode Shortcuts (press Enter to activate)
- **Ctrl + /**: Comment/uncomment selected lines
- **Tab**: Code completion or indent
- **Shift + Tab**: Tooltip (for function arguments)
- **Ctrl + Shift + -**: Split cell at cursor
- **Ctrl + Shift + P**: Command palette (access to all commands)

### Navigation Shortcuts (in both modes)
- **Up Arrow / Down Arrow**: Move up/down one cell
- **Ctrl + Home**: Go to first cell
- **Ctrl + End**: Go to last cell
- **Ctrl + G**: Go to specific cell by number
- **Shift + L**: Toggle line numbers

### Other Useful Shortcuts
- **Esc + F**: Find and replace
- **Esc + O**: Toggle cell output
- **Esc + H**: Show keyboard shortcuts help dialog
- **Esc + I, I**: Interrupt kernel
- **Esc + 0, 0**: Restart kernel
- **Ctrl + Shift + Enter**:Run All Cells

---

# [Pandas](https://github.com/akashdip2001/ML-Machine-Learning/tree/main/pandas)

### Downlod [Pythin](https://www.python.org/downloads/_)

Run Command Prompt as Administrator:

  - Right-click on the Command Prompt icon in the Start menu.
  - Select "Run as administrator".
  - Confirm the User Account Control prompt if prompted.

```python
!pip install pandas
!pip install jupyter
# If you want to install matplotlib as well, uncomment the line below
# !pip install matplotlib

!jupyter notebook --version

```

```
jupyter notebook
```
![Screenshot (38)](https://github.com/akashdip2001/ML-Machine-Learning/assets/81384987/bd3b3e3a-5d70-41a2-b412-14f1f109fc8e)

![Screenshot (39)](https://github.com/akashdip2001/ML-Machine-Learning/assets/81384987/d1b0208d-eca9-42d1-a800-8ca1cda97eb4)

```python
import numpy as np
import matplotlib.pyplot as plt

# Data for plotting
t = np.arange(0.0, 2.0, 0.01)
s = 1 + np.sin(2 * np.pi * t)

fig, ax = plt.subplots()
ax.plot(t, s)

ax.set(xlabel='time (s)', ylabel='voltage (mV)',
       title='About as simple as it gets, folks')
ax.grid()

plt.show()
```


    
![png](https://github.com/akashdip2001/ML-Machine-Learning/raw/main/pandas/output_0_0.png)

| more about [pamdas](https://github.com/akashdip2001/ML-Machine-Learning/tree/main/pandas) |
|---

# [numPy](https://github.com/akashdip2001/ML-Machine-Learning/tree/main/numPy)

#### [documentation](https://numpy.org/doc/stable/reference/)

```python
pip install numpy
python.exe -m pip install --upgrade pip

pip install jupyter
```


| python 10h => |🍭 [SourceCode](https://github.com/akashdip2001/Python-Course-10h) 🍭|🐥 [Notes 10h]() 🐥|❌ [complete Notes](https://www.codewithharry.com/notes/) ❌|
|-------------------- |-------------------- |-------------------- |-------------------- |

```html
7296

body {
            zoom: 100%; /* Default zoom level */
        }

<script>
        function isPC() {
            return !/Mobi|Android/i.test(navigator.userAgent);
        }

        function setZoom() {
            if (isPC()) {
                document.body.style.zoom = "150%";
            }
        }

        window.onload = setZoom;
    </script>



7522

<div style="text-align: right;">
        <img src="pandas/img/Python-Pandas-logo.png" alt="Pandas Logo" width="300" />
        <div style="font-size: 10px; margin-top: -10px; margin-bottom: 15px;">by Akashdip Mahapatra</div>
    </div>
```
