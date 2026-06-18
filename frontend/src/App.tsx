import { FormEvent, useState } from 'react'
import './index.css'

const benefits = [
  { icon: '路', text: '東京の静かな場所の紹介' },
  { icon: '物', text: '日本文化の小さな物語' },
  { icon: '時', text: '時間を大切にするためのヒント' },
  { icon: '写', text: 'フィルムカメラの楽しさ' },
  { icon: '泊', text: '東京で体験できる宿泊・散策案' },
]

const galleryItems = [
  {
    src: 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=900&q=80',
    alt: '夕暮れの東京の路地',
    caption: '夕暮れ、音が少し遠のく路地。',
  },
  {
    src: 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=80',
    alt: '木製テーブルの上のクラシックカメラ',
    caption: '古いカメラが教えてくれる、待つ楽しみ。',
  },
  {
    src: 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=900&q=80',
    alt: '静かな日本の街並み',
    caption: '観光地のすぐ隣にある、静かな東京。',
  },
]

const voices = [
  '朝のコーヒーを飲みながら読むと、週末の過ごし方が少し丁寧になります。東京に住んでいても知らない場所が多いと気づきました。',
  '宿泊先から歩ける小さな路地の紹介が心に残りました。旅程を詰め込まない旅の良さを思い出せます。',
  'フィルムカメラの話が懐かしく、写真を撮る時間そのものを楽しめるようになりました。',
]

function NewsletterForm({ id }: { id: string }) {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmedEmail = email.trim()

    if (!trimmedEmail) {
      setMessage('メールアドレスを入力してください。')
      return
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      setMessage('有効なメールアドレスを入力してください。')
      return
    }

    setMessage('ご登録ありがとうございます。次回のレターをお楽しみに。')
    setEmail('')
  }

  return (
    <form className="newsletter-form" onSubmit={handleSubmit} noValidate>
      <label className="sr-only" htmlFor={id}>
        メールアドレス
      </label>
      <input
        id={id}
        type="email"
        placeholder="メールアドレスを入力"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        aria-describedby={`${id}-message`}
      />
      <button type="submit">無料レターを受け取る</button>
      <p id={`${id}-message`} className="form-message" aria-live="polite">
        {message}
      </p>
    </form>
  )
}

export default function App() {
  return (
    <div className="landing-page">
      <header className="hero">
        <img
          className="hero-image"
          src="https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=1800&q=85"
          alt="静かな東京の路地"
        />
        <div className="hero-overlay" />
        <div className="hero-content">
          <p className="eyebrow">Tokyo Serene Days</p>
          <h1>時間を取り戻す旅へ。</h1>
          <p className="hero-copy">
            東京には、まだ静かな時間が残っています。毎週1回、東京の隠れた場所と時間を大切にするヒントをお届けします。
          </p>
          <NewsletterForm id="hero-email" />
        </div>
      </header>

      <main>
        <section className="section narrow">
          <p className="eyebrow">Question</p>
          <h2>なぜ私たちはいつも急いでいるのか</h2>
          <p>
            朝から夜まで届く通知、次々に埋まる予定、止まらない情報の流れ。便利になったはずの暮らしの中で、私たちは立ち止まる余白を少しずつ手放してきました。東京の静かな路地や小さな店、古いカメラのシャッター音に耳を澄ませることは、自分の時間を取り戻すための小さな入口です。
          </p>
        </section>

        <section className="section story-section">
          <div className="story-text">
            <p className="eyebrow">Founder Story</p>
            <h2>12年間の会社員生活を辞めて気づいたこと</h2>
            <p>
              私はエンジニアとして12年間働いた後、家族との時間を大切にしたいと考え独立しました。東京を歩きながら気づいたのは、本当に豊かな人は時間を大切にしているということでした。
            </p>
            <p>
              Tokyo Serene Daysでは、急がない旅、余白のある暮らし、写真を待つ楽しさを、毎週のレターとして丁寧にお届けします。
            </p>
          </div>
          <figure className="founder-card">
            <div className="founder-placeholder">Photo / Memo</div>
            <figcaption>白井丈太郎氏の写真やメモ書き画像を配置できます。</figcaption>
          </figure>
        </section>

        <section className="section">
          <p className="eyebrow">Benefits</p>
          <h2>週1回、こんな内容をお届けします</h2>
          <div className="benefit-grid">
            {benefits.map((benefit) => (
              <article className="benefit-card" key={benefit.text}>
                <span className="benefit-icon" aria-hidden="true">
                  {benefit.icon}
                </span>
                <p>{benefit.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="section gallery-section">
          <p className="eyebrow">Gallery</p>
          <h2>静けさのある風景</h2>
          <div className="gallery-grid">
            {galleryItems.map((item) => (
              <figure className="gallery-item" key={item.caption}>
                <img src={item.src} alt={item.alt} />
                <figcaption>{item.caption}</figcaption>
              </figure>
            ))}
          </div>
        </section>

        <section className="section testimonials-section">
          <p className="eyebrow">Community</p>
          <h2>読者の声</h2>
          <div className="testimonial-grid">
            {voices.map((voice, index) => (
              <article className="testimonial-card" key={voice}>
                <p>「{voice}」</p>
                <span>Reader {index + 1}</span>
              </article>
            ))}
          </div>
        </section>

        <section className="section cta-section" aria-labelledby="cta-title">
          <div className="cta-box">
            <p className="eyebrow">Letter</p>
            <h2 id="cta-title">静かな東京から、週に一度の手紙を。</h2>
            <p>忙しさから少し離れて、時間を大切にする暮らしのヒントを受け取りませんか。</p>
            <NewsletterForm id="cta-email" />
          </div>
        </section>
      </main>

      <footer className="footer">
        <div>
          <p className="footer-brand">Tokyo Serene Days</p>
          <p>運営者: JM CAMERA / 白井丈太郎</p>
          <a href="/privacy">プライバシーポリシー</a>
        </div>
        <nav className="footer-social" aria-label="SNSリンク">
          <a href="https://www.instagram.com/" aria-label="Instagram">Instagram</a>
          <a href="https://www.facebook.com/" aria-label="Facebook">Facebook</a>
          <a href="https://x.com/" aria-label="X">X</a>
        </nav>
        <div className="footer-logos" aria-label="関連ブランド">
          <a href="https://example.com/jm-camera">JM CAMERA</a>
          <a href="https://example.com/jm-stay">JM STAY</a>
          <a href="https://example.com/tokyo-serene-days">Tokyo Serene Days</a>
        </div>
      </footer>
    </div>
  )
}
