import { useMemo, useRef, useState } from 'react'

type PatientForm = {
  name: string
  age: string
  gender: string
  diabetesDuration: string
  sugarLevel: string
}

type PredictResponse = {
  request_id: string
  created_at: string
  image_url: string
  prediction: {
    label: string
    confidence_percent: number
    probabilities_percent: Record<string, number>
    model_mode: string
  }
  report_url: string
}

function getApiBase(): string {
  const v = (import.meta as any).env?.VITE_API_BASE as string | undefined
  return (v && v.trim()) || 'http://localhost:8000'
}

function riskColor(label: string): string {
  if (label === 'No DR') return 'bg-emerald-500'
  if (label === 'Mild') return 'bg-lime-500'
  if (label === 'Moderate') return 'bg-amber-500'
  if (label === 'Severe') return 'bg-orange-500'
  return 'bg-red-600'
}

function clampPercent(v: number): number {
  if (Number.isNaN(v)) return 0
  return Math.max(0, Math.min(100, v))
}

export function App() {
  const apiBase = useMemo(() => getApiBase(), [])

  const [patient, setPatient] = useState<PatientForm>({
    name: '',
    age: '',
    gender: 'Male',
    diabetesDuration: '',
    sugarLevel: '',
  })

  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  const videoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [webcamOn, setWebcamOn] = useState(false)

  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<PredictResponse | null>(null)

  async function startWebcam() {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setWebcamOn(true)
    } catch (e: any) {
      setError(e?.message || 'Webcam permission failed.')
      setWebcamOn(false)
    }
  }

  function stopWebcam() {
    const stream = streamRef.current
    if (stream) {
      stream.getTracks().forEach((t) => t.stop())
    }
    streamRef.current = null
    setWebcamOn(false)
  }

  async function captureFromWebcam() {
    setError(null)
    const video = videoRef.current
    if (!video) return
    const w = video.videoWidth || 640
    const h = video.videoHeight || 480
    const canvas = document.createElement('canvas')
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0, w, h)

    const blob: Blob | null = await new Promise((resolve) =>
      canvas.toBlob((b) => resolve(b), 'image/jpeg', 0.92),
    )
    if (!blob) return

    const file = new File([blob], 'webcam.jpg', { type: 'image/jpeg' })
    setSelectedFile(file)
    const url = URL.createObjectURL(blob)
    setPreviewUrl(url)
  }

  function onPickFile(file: File | null) {
    setSelectedFile(file)
    setResult(null)
    if (!file) {
      setPreviewUrl(null)
      return
    }
    setPreviewUrl(URL.createObjectURL(file))
  }

  async function submit() {
    setError(null)
    setResult(null)

    if (!selectedFile) {
      setError('Please upload or capture a retinal image.')
      return
    }
    if (!patient.name || !patient.age || !patient.diabetesDuration || !patient.sugarLevel) {
      setError('Please fill all patient fields.')
      return
    }

    setBusy(true)
    try {
      const fd = new FormData()
      fd.append('image', selectedFile)
      fd.append('name', patient.name)
      fd.append('age', patient.age)
      fd.append('gender', patient.gender)
      fd.append('diabetes_duration', patient.diabetesDuration)
      fd.append('sugar_level', patient.sugarLevel)

      const res = await fetch(`${apiBase}/predict`, { method: 'POST', body: fd })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || `Request failed with ${res.status}`)
      }
      const json = (await res.json()) as PredictResponse
      setResult(json)
    } catch (e: any) {
      setError(e?.message || 'Prediction failed.')
    } finally {
      setBusy(false)
    }
  }

  const meter = clampPercent(result?.prediction?.confidence_percent ?? 0)
  const label = result?.prediction?.label ?? ''

  return (
    <div className="min-h-full bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight">Eye ROI Analyzer for Diabetic Retinopathy</h1>
          <p className="mt-1 text-sm text-slate-300">
            Upload a retinal image or capture using webcam, then get a stage prediction with confidence and a PDF report.
          </p>
        </header>

        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
            <h2 className="text-lg font-semibold">1) Retinal image</h2>

            <div className="mt-4 grid gap-4">
              <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
                <label className="block text-sm font-medium text-slate-200">Upload image</label>
                <input
                  className="mt-2 block w-full text-sm"
                  type="file"
                  accept="image/*"
                  onChange={(e) => onPickFile(e.target.files?.[0] ?? null)}
                />
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-medium text-slate-200">Webcam capture</div>
                    <div className="text-xs text-slate-400">Works best with good lighting</div>
                  </div>
                  <div className="flex gap-2">
                    {!webcamOn ? (
                      <button
                        type="button"
                        className="rounded-lg bg-slate-200 px-3 py-2 text-sm font-medium text-slate-950 hover:bg-white"
                        onClick={startWebcam}
                      >
                        Start
                      </button>
                    ) : (
                      <button
                        type="button"
                        className="rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium text-slate-100 hover:bg-slate-700"
                        onClick={stopWebcam}
                      >
                        Stop
                      </button>
                    )}
                    <button
                      type="button"
                      className="rounded-lg bg-indigo-500 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-400 disabled:opacity-50"
                      onClick={captureFromWebcam}
                      disabled={!webcamOn}
                    >
                      Capture
                    </button>
                  </div>
                </div>

                <div className="mt-3 overflow-hidden rounded-xl border border-slate-800 bg-black">
                  <video ref={videoRef} className="h-56 w-full object-cover" muted playsInline />
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
                <div className="text-sm font-medium text-slate-200">Preview</div>
                <div className="mt-2 overflow-hidden rounded-xl border border-slate-800 bg-slate-950">
                  {previewUrl ? (
                    <img src={previewUrl} alt="Preview" className="h-64 w-full object-contain" />
                  ) : (
                    <div className="flex h-64 items-center justify-center text-sm text-slate-400">
                      No image selected
                    </div>
                  )}
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
            <h2 className="text-lg font-semibold">2) Patient form</h2>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className="text-sm text-slate-200">Name</label>
                <input
                  className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                  value={patient.name}
                  onChange={(e) => setPatient((p) => ({ ...p, name: e.target.value }))}
                  placeholder="Patient name"
                />
              </div>

              <div>
                <label className="text-sm text-slate-200">Age</label>
                <input
                  className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                  value={patient.age}
                  onChange={(e) => setPatient((p) => ({ ...p, age: e.target.value }))}
                  placeholder="e.g. 45"
                  inputMode="numeric"
                />
              </div>

              <div>
                <label className="text-sm text-slate-200">Gender</label>
                <select
                  className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                  value={patient.gender}
                  onChange={(e) => setPatient((p) => ({ ...p, gender: e.target.value }))}
                >
                  <option>Male</option>
                  <option>Female</option>
                  <option>Other</option>
                </select>
              </div>

              <div>
                <label className="text-sm text-slate-200">Diabetes duration (years)</label>
                <input
                  className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                  value={patient.diabetesDuration}
                  onChange={(e) => setPatient((p) => ({ ...p, diabetesDuration: e.target.value }))}
                  placeholder="e.g. 8"
                  inputMode="decimal"
                />
              </div>

              <div>
                <label className="text-sm text-slate-200">Sugar level (mg/dL)</label>
                <input
                  className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                  value={patient.sugarLevel}
                  onChange={(e) => setPatient((p) => ({ ...p, sugarLevel: e.target.value }))}
                  placeholder="e.g. 180"
                  inputMode="decimal"
                />
              </div>
            </div>

            <div className="mt-5 flex items-center gap-3">
              <button
                type="button"
                className="rounded-xl bg-indigo-500 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-400 disabled:opacity-60"
                onClick={submit}
                disabled={busy}
              >
                {busy ? 'Analyzing…' : 'Analyze'}
              </button>

              <div className="text-xs text-slate-400">
                API: <span className="text-slate-200">{apiBase}</span>
              </div>
            </div>

            {error ? (
              <div className="mt-4 rounded-xl border border-red-800/60 bg-red-950/40 p-3 text-sm text-red-200">
                {error}
              </div>
            ) : null}

            {result ? (
              <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-950/40 p-4">
                <div className="flex flex-wrap items-end justify-between gap-3">
                  <div>
                    <div className="text-sm text-slate-300">Prediction</div>
                    <div className="text-xl font-semibold">{result.prediction.label}</div>
                    <div className="mt-1 text-xs text-slate-400">
                      Mode: <span className="text-slate-200">{result.prediction.model_mode}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-slate-300">Confidence</div>
                    <div className="text-xl font-semibold">{result.prediction.confidence_percent.toFixed(2)}%</div>
                  </div>
                </div>

                <div className="mt-4">
                  <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
                    <span>Risk meter</span>
                    <span>{meter.toFixed(0)}%</span>
                  </div>
                  <div className="h-3 w-full overflow-hidden rounded-full bg-slate-800">
                    <div className={`h-3 ${riskColor(label)}`} style={{ width: `${meter}%` }} />
                  </div>
                </div>

                <div className="mt-4 grid gap-2 text-sm">
                  <div className="flex items-center justify-between text-slate-300">
                    <span>PDF report</span>
                    <a
                      className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 hover:bg-slate-800"
                      href={`${apiBase}${result.report_url}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open
                    </a>
                  </div>
                </div>
              </div>
            ) : (
              <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-950/20 p-4 text-sm text-slate-400">
                Results will appear here after analysis.
              </div>
            )}
          </section>
        </div>

        <footer className="mt-8 text-xs text-slate-400">
          This demo app stores images in Azure Blob (if configured) or locally, and stores metadata in Cosmos DB (Mongo API)
          or a local JSON file fallback.
        </footer>
      </div>
    </div>
  )
}

