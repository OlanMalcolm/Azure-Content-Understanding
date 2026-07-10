# /src

This folder is for source code and demo code associated with your session.

## What goes here

- Sample applications or scripts demonstrated during the session
- Starter code that attendees can use as a starting point
- Solution code for completed exercises

## Tips

- Include a README or comments explaining how to run the code
- If your session doesn't include source code, feel free to remove this folder

## Synthetic clinical test data

The healthcare notebook expects five PDFs in each clinical category. To generate
a local, no-PHI test pack when the optional public datasets have not been
downloaded, run this from the repository root:

```powershell
uv run --project demo-app --locked python src\generate_synthetic_clinical_data.py
```

This creates 35 clearly labelled fictional PDFs under
`src\sample-data\cnh-clinical\`. The files are ignored by Git. They support
workflow, classifier, and custom-analyzer testing but do not replace the
handwriting or image-rich examples in the public datasets.
