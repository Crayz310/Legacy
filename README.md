<a href="https://www.codacy.com/gh/Crayz310/Legacy/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Crayz310/Legacy&amp;utm_campaign=Badge_Grade"><img src="https://app.codacy.com/project/badge/Grade/97e3ea868f9344a5aa6e4d874f83db14"/></a>
<a href="#"><img src="https://img.shields.io/github/languages/code-size/Crayz310/Legacy"/></a>
<a href="#"><img src="https://img.shields.io/github/issues-raw/Crayz310/Legacy"/></a>
<a href="#"><img src="https://img.shields.io/github/license/Crayz310/Legacy"/></a>
<a href="#"><img src="https://img.shields.io/github/commit-activity/m/Crayz310/Legacy"/></a><br>
<a href="#"><img src="https://img.shields.io/github/forks/Crayz310/Legacy?style=flat"/></a>
<a href="#"><img src="https://img.shields.io/github/stars/Crayz310/Legacy"/></a>&nbsp;<a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black"></a><br>

### Disclaimer

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/efd3ba8ed62942049006b06f6808d61b)](https://app.codacy.com/gh/Crayz310/Legacy?utm_source=github.com&utm_medium=referral&utm_content=Crayz310/Legacy&utm_campaign=Badge_Grade)

> If you are a paranoid person, you should not use this userbot. This userbot is not a virus, but it can be used for malicious purposes. You are responsible for all actions taken by your account.

<hr>
<h2><img src="https://img.icons8.com/?size=100&id=Jd0d5Iz2TZIb&format=png&color=000000" height="54" align="center" style="margin-right: 7px;">Installation</h2>

<b>⚙ Manual installation (no script):</b><br>
```bash
apt update && apt install git python3 -y && git clone https://github.com/Crayz310/Legacy && cd Legacy && pip install -r requirements.txt && python3 -m legacy
```

<i>If you are on VPS\VDS, type <code>--proxy-pass</code> in the end of command to open SSH tunnel to your Legacy web interface, or use <code>--no-web</code> to complete setup in console</i><br>

<b>🐬 Docker:</b><br>
```bash
git clone https://github.com/Crayz310/Legacy && cd Legacy && sudo docker build . -t Crayz310/Legacy:latest
```

```bash
sudo docker run --restart=unless-stopped --name <container name> -p <port>:8080 --detach -it Crayz310/Legacy:latest
```
<hr>
<h2><img src="https://img.icons8.com/?size=100&id=PClBimo4GQGJ&format=png&color=000000" height="54" align="center" style="margin-right: 7px;"> Changes</h2>

<ul>
 <li>🆕 <b>Latest Telegram layer</b> with reactions, video stickers and other stuff</li>
 <li>🔓 <b>Security</b> improvements, including <b>native entity caching</b> and <b>targeted security rules</b></li>
 <li>🎨 <b>UI/UX</b> improvements</li>
 <li>📼 Improved and new <b>core modules</b></li>
 <li>⏱ Quick <b>bug fixes</b></li>
 <li>▶️ <b>Inline forms, galleries and lists</b></li>
 <li>🔁 Full <b>backward compatibility</b> with FTG, Hikka and GeekTG modules</li>
</ul>

<hr>
<h2 border="none"><img src="https://img.icons8.com/?size=100&id=5cJddikxEAhI&format=png&color=000000" height="54" align="center" style="margin-right: 7px;"> Requirements</h2>
<ul>
 <li>🐍 Python 3.9-3.12</li>
 <li>🔑 API_ID and HASH from <a href="https://my.telegram.org/apps" color="#2594cb">Telegram</a></li>
</ul>

<hr>
<h2 border="none"><img src="https://img.icons8.com/?size=100&id=rLMbY01ZXrPE&format=png&color=000000" height="54" align="center" style="margin-right: 7px;"> Documentation</h2>

Check out <a href="https://web.archive.org/dev.hikka.pw">dev.hikka.pw</a> for developers' documentation and <a href="https://web.archive.org/hikka.pw">hikka.pw</a> for users' documentation<br>

<hr>
<h2 border="none"><img src="https://img.icons8.com/?size=100&id=wuPAd75eU6lM&format=png&color=000000" height="54" align="center" style="margin-right: 7px;"> <a href="https://t.me/legacy_help">Support</a></h2>

<hr>
<h2 border="none"><img src="https://img.icons8.com/?size=100&id=YCbKhwUNH1pc&format=png&color=000000" height="54" align="center" style="margin-right: 7px;"> Features</h2>
<table>
 <tr>
  <td>
   <img src="https://github.com/hikariatama/assets/raw/master/1286-three-3-key-flat.webp" height="32" align="middle"><b> Forms - bored of writing? Use buttons!</b>
  </td>
  <td>
   <img src="https://github.com/hikariatama/assets/raw/master/61-camera-flat.webp" height="32" align="middle"><b> Galleries - scroll your favorite photos in Telegram</b>
  </td>
 </tr>
 <tr>
  <td>
   <img src="https://i.postimg.cc/T3VSMbvQ/legacy-inline-form.gif">
  </td>
  <td>
   <img src="https://i.postimg.cc/1XDTmVN9/legacy-inline.gif">
  </td>
 </tr>
</table>
<table>
 <tr>
  <td>
   <img src="https://github.com/hikariatama/assets/raw/master/216-arrow-5-flat.webp" height="32" align="middle"><b> Inline - share userbot with your friends</b>
  </td>
  <td>
   <img src="https://github.com/hikariatama/assets/raw/master/1054-amazon-echo-speaker-flat.webp" height="32" align="middle"><b> Bot interactions - "No PM"? No problem. Feedback bot at your service</b>
  </td>
 </tr>
 <tr>
  <td>
   <img src="https://i.postimg.cc/nzGcXrm1/legacy-inline-cmds.gif">
  </td>
  <td>
   <img src="https://i.postimg.cc/HsXHnVC8/legacy-feedback.gif">
  </td>
 </tr>
</table>
<table>
 <tr>
  <td>
   <img src="https://github.com/hikariatama/assets/raw/master/1140-error-flat.webp" height="32" align="middle"><b> InlineLogs - traceback directly in message, caused error</b>
  </td>
  <td>
   <img src="https://github.com/hikariatama/assets/raw/master/35-edit-flat.webp" height="32" align="middle"><b> Grep - execute command and get only required lines</b>
  </td>
 </tr>
 <tr>
  <td>
   <img src="https://i.postimg.cc/FHHPqBGF/legacy-inline-logs.gif">
  </td>
  <td>
   <img src="https://i.postimg.cc/FzbcshFt/legacy-grep.gif">
  </td>
 </tr>
</table>

<b>👨‍👦 NoNick, NoNickUser, NoNickCmd, NoNickChat - use another account for userbot</b>
<img src="https://i.postimg.cc/wvX3DFCL/legacy-nonick.gif">

<hr>

### Warning

> This project is provided as-is. Developer doesn't take ANY responsibility over any problems, caused by userbot. By installing Legacy you take all risks on you. This is but not limited to account bans, deleted (by Telegram algorithms) messages, SCAM-modules, leaked sessions (due to SCAM-modules). It is **highly** recommended to enable the API Flood protection (.api_fw_protection) and not to install many modules at once. By using Legacy you give your consent to any actions made by your account in background in purposes of automatization. Please, consider reading https://core.telegram.org/api/terms for more information.

<hr>
<h2><img src="https://img.icons8.com/?size=100&id=haPxINLo0tRS&format=png&color=000000" height="54" align="center" style="margin-right: 7px;">Special thanks to:</h2>

<ul>
    <li><a href="https://gitlab.com/hackintosh5">Hackintosh5</a> for FTG, which is the base of Hikka</li>
    <li><a href="https://github.com/beveiled">Hikariatama</a> for Hikka, which is the base of project</li>
    <li><a href="https://github.com/coddrago">Codrago</a> for Heroku <b>(Some patches were taken from Heroku v1.6.8)</b></li>
    <li><a href="https://t.me/GunyaKshin">Codwiz</a> for Ukrainian translation pack</li>
    <li><a href="https://t.me/Admt_450">ɴᴇᴛ『s』ᴛᴀʟᴋ『2』『4』</a> for testing, finding bugs and Ukrainian translation</li>
    <li><a href="https://t.me/lonami">Lonami</a> for Telethon, which is the base of Legacy-TL-New</li>
</ul>
