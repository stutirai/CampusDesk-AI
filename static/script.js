// ---------------------------------------------------------------------
// PWA: register service worker
// ---------------------------------------------------------------------

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/service-worker.js')
      .catch(() => {});
  });
}


// ---------------------------------------------------------------------
// DOM ELEMENTS
// ---------------------------------------------------------------------

const form = document.getElementById('chat-form');
const input = document.getElementById('user-input');
const log = document.getElementById('log');

const micBtn = document.getElementById('mic-btn');
const themeToggle = document.getElementById('theme-toggle');

const pdfUpload = document.getElementById('pdf-upload');
const imageUpload = document.getElementById('image-upload');

const uploadStatus = document.getElementById('upload-status');

const pdfActions = document.getElementById('pdf-actions');
const pdfActionButtons =
  document.querySelectorAll('.pdf-action');

const historyList =
  document.getElementById('history-list');

const historyToggle =
  document.getElementById('history-toggle');

const sidebar =
  document.querySelector('.sidebar');


let conversationHistory = [];


// ---------------------------------------------------------------------
// THEME TOGGLE
// ---------------------------------------------------------------------

function applyTheme(theme) {

  document.documentElement.setAttribute(
    'data-theme',
    theme
  );

  themeToggle.textContent =
    theme === 'dark'
      ? '☀️'
      : '🌙';

  localStorage.setItem(
    'campusdesk-theme',
    theme
  );
}


applyTheme(
  localStorage.getItem('campusdesk-theme') || 'light'
);


themeToggle.addEventListener('click', () => {

  const current =
    document.documentElement.getAttribute(
      'data-theme'
    );

  applyTheme(
    current === 'dark'
      ? 'light'
      : 'dark'
  );

});


// ---------------------------------------------------------------------
// SIDEBAR / HISTORY TOGGLE
// ---------------------------------------------------------------------

historyToggle.addEventListener('click', () => {

  sidebar.classList.toggle('open');

});


// ---------------------------------------------------------------------
// ADD QUESTION TO HISTORY
// ---------------------------------------------------------------------

function addToHistory(question) {

  const empty =
    historyList.querySelector(
      '.history-empty'
    );

  if (empty) {
    empty.remove();
  }


  const item =
    document.createElement('button');

  item.className =
    'history-item';

  item.textContent =
    question;

  item.title =
    question;


  item.onclick = () => {

    askSuggested(question);

  };


  historyList.prepend(item);

}


// ---------------------------------------------------------------------
// TEXT TO SPEECH
// ---------------------------------------------------------------------

function speakText(text) {

  if (!('speechSynthesis' in window)) {
    return;
  }

  window.speechSynthesis.cancel();


  const utterance =
    new SpeechSynthesisUtterance(text);

  utterance.rate = 1;
  utterance.pitch = 1;


  window.speechSynthesis.speak(
    utterance
  );

}


// ---------------------------------------------------------------------
// CHAT LOG
// ---------------------------------------------------------------------

function clearEmptyState() {

  const empty =
    log.querySelector('.empty-state');

  if (empty) {
    empty.remove();
  }

}


function addMessage(text, sender) {

  clearEmptyState();


  const row =
    document.createElement('div');

  row.className =
    `row ${sender}`;


  const msg =
    document.createElement('div');

  msg.className =
    'msg';


  const tag =
    document.createElement('span');

  tag.className =
    'tag';

  tag.textContent =
    sender === 'user'
      ? 'You'
      : 'CampusDesk AI';


  msg.appendChild(tag);


  msg.appendChild(
    document.createTextNode(text)
  );


  // ---------------------------------------------------------------
  // BOT ACTIONS
  // ---------------------------------------------------------------

  if (sender === 'bot' && text) {

    const actions =
      document.createElement('div');

    actions.className =
      'msg-actions';


    // COPY

    const copyBtn =
      document.createElement('button');

    copyBtn.className =
      'copy-btn';

    copyBtn.textContent =
      'Copy';


    copyBtn.onclick =
      async () => {

        try {

          await navigator.clipboard.writeText(
            text
          );

          copyBtn.textContent =
            'Copied';

          setTimeout(() => {

            copyBtn.textContent =
              'Copy';

          }, 1500);

        } catch {

          copyBtn.textContent =
            'Copy failed';

          setTimeout(() => {

            copyBtn.textContent =
              'Copy';

          }, 1500);

        }

      };


    // LISTEN

    const listenBtn =
      document.createElement('button');

    listenBtn.className =
      'copy-btn';

    listenBtn.textContent =
      'Listen';


    listenBtn.onclick =
      () => {

        speakText(text);

      };


    actions.appendChild(
      copyBtn
    );

    actions.appendChild(
      listenBtn
    );

    msg.appendChild(
      actions
    );

  }


  row.appendChild(msg);

  log.appendChild(row);


  log.scrollTop =
    log.scrollHeight;


  return row;

}


// ---------------------------------------------------------------------
// SUGGESTED QUESTIONS
// ---------------------------------------------------------------------

function askSuggested(question) {

  input.value =
    question;

  form.dispatchEvent(
    new Event('submit')
  );

}


window.askSuggested =
  askSuggested;


// ---------------------------------------------------------------------
// NORMAL CHAT
// ---------------------------------------------------------------------

form.addEventListener(
  'submit',
  async (e) => {

    e.preventDefault();


    const question =
      input.value.trim();


    if (!question) {
      return;
    }


    addMessage(
      question,
      'user'
    );


    addToHistory(
      question
    );


    input.value =
      '';


    const typingRow =
      addMessage(
        '',
        'bot'
      );


    const typingMsg =
      typingRow.querySelector(
        '.msg'
      );


    typingMsg.innerHTML +=
      `
      <span class="dots">
        <span></span>
        <span></span>
        <span></span>
      </span>
      `;


    try {

      const res =
        await fetch(
          '/chat',
          {
            method: 'POST',

            headers: {
              'Content-Type':
                'application/json'
            },

            body: JSON.stringify({

              message:
                question,

              history:
                conversationHistory

            })

          }
        );


      if (!res.ok) {
        throw new Error(
          'Server error'
        );
      }


      const data =
        await res.json();


      typingRow.remove();


      addMessage(
        data.reply,
        'bot'
      );


      conversationHistory.push({

        role: 'user',

        text: question

      });


      conversationHistory.push({

        role: 'bot',

        text: data.reply

      });


      if (
        conversationHistory.length > 20
      ) {

        conversationHistory =
          conversationHistory.slice(
            -20
          );

      }

    } catch (err) {

      console.error(err);


      typingRow.remove();


      addMessage(
        'Something went wrong. Please try again.',
        'bot'
      );

    }

  }
);


// ---------------------------------------------------------------------
// VOICE INPUT
// ---------------------------------------------------------------------

if (
  'webkitSpeechRecognition' in window ||
  'SpeechRecognition' in window
) {

  const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;


  const recognition =
    new SpeechRecognition();


  recognition.continuous =
    false;

  recognition.lang =
    'en-US';


  let listening =
    false;


  micBtn.addEventListener(
    'click',
    () => {

      if (listening) {
        return;
      }


      recognition.start();


      listening =
        true;


      micBtn.classList.add(
        'listening'
      );


      micBtn.textContent =
        '●';

    }
  );


  recognition.onresult =
    (event) => {

      input.value =
        event
          .results[0][0]
          .transcript;

    };


  recognition.onend =
    () => {

      listening =
        false;


      micBtn.classList.remove(
        'listening'
      );


      micBtn.textContent =
        '🎤';

    };


  recognition.onerror =
    () => {

      listening =
        false;


      micBtn.classList.remove(
        'listening'
      );


      micBtn.textContent =
        '🎤';

    };

} else {

  micBtn.style.display =
    'none';

}


// ---------------------------------------------------------------------
// PDF UPLOAD
// ---------------------------------------------------------------------

pdfUpload.addEventListener(
  'change',
  async () => {

    const file =
      pdfUpload.files[0];


    if (!file) {
      return;
    }


    // Hide actions while uploading

    pdfActions.hidden =
      true;


    uploadStatus.textContent =
      `Uploading "${file.name}"...`;


    const formData =
      new FormData();


    formData.append(
      'file',
      file
    );


    try {

      const res =
        await fetch(
          '/upload',
          {
            method: 'POST',
            body: formData
          }
        );


      if (!res.ok) {

        throw new Error(
          'PDF upload failed'
        );

      }


      const data =
        await res.json();


      if (data.success) {

        uploadStatus.textContent =
          `✓ ${data.filename} — PDF ready`;


        const pdfLabel =
          document.querySelector(
            'label[for="pdf-upload"]'
          );


        if (pdfLabel) {

          pdfLabel.classList.add(
            'uploaded'
          );

        }


        // -----------------------------------------------------------
        // SHOW SMART PDF ACTIONS
        // -----------------------------------------------------------

        pdfActions.hidden =
          false;


      } else {

        uploadStatus.textContent =
          `Upload failed: ${data.message}`;

      }

    } catch (err) {

      console.error(err);


      uploadStatus.textContent =
        'PDF upload failed. Please try again.';

    }


    pdfUpload.value =
      '';

  }
);


// ---------------------------------------------------------------------
// IMAGE UPLOAD
// ---------------------------------------------------------------------

imageUpload.addEventListener(
  'change',
  async () => {

    const file =
      imageUpload.files[0];


    if (!file) {
      return;
    }


    uploadStatus.textContent =
      `Uploading "${file.name}"...`;


    const formData =
      new FormData();


    formData.append(
      'file',
      file
    );


    try {

      const res =
        await fetch(
          '/upload-image',
          {
            method: 'POST',
            body: formData
          }
        );


      if (!res.ok) {

        throw new Error(
          'Image upload failed'
        );

      }


      const data =
        await res.json();


      if (data.success) {

        uploadStatus.textContent =
          `✓ ${data.filename} — image ready`;


        const imageLabel =
          document.querySelector(
            'label[for="image-upload"]'
          );


        if (imageLabel) {

          imageLabel.classList.add(
            'uploaded'
          );

        }

      } else {

        uploadStatus.textContent =
          `Upload failed: ${data.message}`;

      }

    } catch (err) {

      console.error(err);


      uploadStatus.textContent =
        'Image upload failed. Please try again.';

    }


    imageUpload.value =
      '';

  }
);


// ---------------------------------------------------------------------
// SMART PDF ACTIONS
// ---------------------------------------------------------------------

pdfActionButtons.forEach(
  (button) => {

    button.addEventListener(
      'click',
      async () => {

        const action =
          button.dataset.action;


        if (!action) {
          return;
        }


        // -----------------------------------------------------------
        // Disable all buttons while processing
        // -----------------------------------------------------------

        pdfActionButtons.forEach(
          (btn) => {

            btn.disabled =
              true;

          }
        );


        const originalText =
          button.innerHTML;


        button.innerHTML =
          `
          <span class="action-icon">⏳</span>

          <span>
            <strong>Working...</strong>
            <small>Analyzing your PDF</small>
          </span>
          `;


        // -----------------------------------------------------------
        // Show a temporary message
        // -----------------------------------------------------------

        const actionNames = {

          summarize:
            'Summarize this PDF',

          mcqs:
            'Generate MCQs from this PDF',

          exam_prep:
            'Create an exam-prep guide',

          key_points:
            'Extract the key points'

        };


        const userRequest =
          actionNames[action] ||
          'Analyze this PDF';


        addMessage(
          userRequest,
          'user'
        );


        const typingRow =
          addMessage(
            '',
            'bot'
          );


        const typingMsg =
          typingRow.querySelector(
            '.msg'
          );


        typingMsg.innerHTML +=
          `
          <span class="dots">
            <span></span>
            <span></span>
            <span></span>
          </span>
          `;


        try {

          const res =
            await fetch(
              '/pdf-action',
              {
                method: 'POST',

                headers: {
                  'Content-Type':
                    'application/json'
                },

                body: JSON.stringify({
                  action: action
                })

              }
            );


          if (!res.ok) {

            throw new Error(
              'PDF action failed'
            );

          }


          const data =
            await res.json();


          typingRow.remove();


          if (data.success) {

            addMessage(
              data.reply,
              'bot'
            );


            // Save action in conversation history

            conversationHistory.push({

              role: 'user',

              text: userRequest

            });


            conversationHistory.push({

              role: 'bot',

              text: data.reply

            });


            if (
              conversationHistory.length > 20
            ) {

              conversationHistory =
                conversationHistory.slice(
                  -20
                );

            }

          } else {

            addMessage(
              data.message ||
                'Could not process the PDF.',
              'bot'
            );

          }

        } catch (err) {

          console.error(err);


          typingRow.remove();


          addMessage(
            'Something went wrong while analyzing the PDF. Please try again.',
            'bot'
          );

        } finally {

          // ---------------------------------------------------------
          // Restore buttons
          // ---------------------------------------------------------

          pdfActionButtons.forEach(
            (btn) => {

              btn.disabled =
                false;

            }
          );


          button.innerHTML =
            originalText;

        }

      }
    );

  }
);