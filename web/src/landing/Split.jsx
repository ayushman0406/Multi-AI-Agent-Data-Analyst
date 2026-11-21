import { Fragment } from 'react'

/** Heading whose words can be staggered in. Screen readers get the unsplit text. */
export default function Split({ as: Tag = 'h2', text, className, id, children }) {
  const words = text.split(' ')
  return (
    <Tag className={className} id={id} data-split="">
      <span className="sr-only">{text}</span>
      <span aria-hidden="true">
        {words.map((w, i) => (
          <Fragment key={i}><span className="w"><span className="wi">{w}</span></span>{i < words.length - 1 ? ' ' : ''}</Fragment>
        ))}
      </span>
      {children}
    </Tag>
  )
}
