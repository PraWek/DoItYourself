; Осторожно приближается и бьёт молнией с дальней дистанции.

(define (step-toward from to)
  (cond ((< from to) 1)
        ((> from to) -1)
        (else 0)))

(define (advance)
  (let ((dx (step-toward (get (position) 0) (get (enemy-position) 0)))
        (dy (step-toward (get (position) 1) (get (enemy-position) 1))))
    (try (move dx dy)
         (lambda (reason)
           (try (move dx 0)
                (lambda (reason) (move 0 dy)))))))

(define (turn)
  (if (and (visible?)
           (<= (distance) (spell-range "молния"))
           (>= (mana) (spell-cost "молния")))
      (cast "молния"
            (get (enemy-position) 0)
            (get (enemy-position) 1))
      (advance)))
